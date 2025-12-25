// Copyright 2023 Divy Srivastava <dj.srivastava23@gmail.com>
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

use base64::engine::general_purpose;
use base64::Engine;
use dora_node_api::arrow::array::{Array, AsArray};
use dora_node_api::arrow::datatypes::DataType;
use dora_node_api::dora_core::config::DataId;
use dora_node_api::dora_core::config::NodeId;
use dora_node_api::into_vec;
use dora_node_api::DoraNode;
use dora_node_api::EventStream;
use dora_node_api::IntoArrow;
use dora_node_api::MetadataParameters;
use rubato::{Resampler, SincFixedIn, SincInterpolationType, SincInterpolationParameters, WindowFunction};
use fastwebsockets::upgrade;
use fastwebsockets::Frame;
use fastwebsockets::OpCode;
use fastwebsockets::Payload;
use tokio::process::Command;
use fastwebsockets::WebSocketError;
use futures_concurrency::future::Race;
use futures_util::future;
use futures_util::future::Either;
use futures_util::FutureExt;
use http_body_util::Empty;
use hyper::body::Bytes;
use hyper::body::Incoming;
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper::Request;
use hyper::Response;
use serde;
use serde::Deserialize;
use serde::Serialize;
use serde_json;
use tokio::net::TcpListener;
use std::sync::Arc;
use tokio::sync::Mutex;
use once_cell::sync::OnceCell;

// Global state for sharing the Dora node connection across WebSocket clients
static DORA_NODE: OnceCell<Arc<Mutex<DoraNode>>> = OnceCell::new();
static DORA_EVENTS: OnceCell<Arc<Mutex<EventStream>>> = OnceCell::new();
static MAAS_PID: OnceCell<Arc<Mutex<Option<u32>>>> = OnceCell::new();

// Helper function for hybrid logging - tries send_log first, falls back to println
#[allow(dead_code)]
fn log_message(node_opt: Option<&mut DoraNode>, level: &str, message: &str) {
    if let Some(node) = node_opt {
        // Try to send through dora logging system
        let log_data = serde_json::json!({
            "node": "websocket-server",
            "level": level,
            "message": message
        });
        
        if let Err(_) = node.send_output(
            DataId::from("log".to_string()),
            Default::default(),
            serde_json::to_string(&log_data).unwrap().into_arrow(),
        ) {
            // Fallback to println if node output fails
            println!("[{}] {}", level, message);
        }
    } else {
        // No node available, use println
        println!("[{}] {}", level, message);
    }
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ErrorDetails {
    pub code: Option<String>,
    pub message: String,
    pub param: Option<String>,
    #[serde(rename = "type")]
    pub error_type: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(tag = "type")]
pub enum OpenAIRealtimeMessage {
    #[serde(rename = "session.update")]
    SessionUpdate { session: SessionConfig },
    #[serde(rename = "input_audio_buffer.append")]
    InputAudioBufferAppend {
        audio: String, // base64 encoded audio
    },
    #[serde(rename = "input_audio_buffer.commit")]
    InputAudioBufferCommit,
    #[serde(rename = "response.create")]
    ResponseCreate { response: ResponseConfig },
    #[serde(rename = "conversation.item.create")]
    ConversationItemCreate { item: ConversationItem },
    #[serde(rename = "conversation.item.truncate")]
    ConversationItemTruncate {
        item_id: String,
        content_index: u32,
        audio_end_ms: u32,
        #[serde(skip_serializing_if = "Option::is_none")]
        event_id: Option<String>,
    },
    // Gracefully ignore unknown/unsupported client events
    #[serde(other)]
    Other,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SessionConfig {
    pub modalities: Vec<String>,
    pub instructions: String,
    pub voice: String,
    pub model: String,
    pub input_audio_format: String,
    pub output_audio_format: String,
    pub input_audio_transcription: Option<TranscriptionConfig>,
    pub turn_detection: Option<TurnDetectionConfig>,
    pub tools: Vec<serde_json::Value>,
    pub tool_choice: String,
    pub temperature: f32,
    pub max_response_output_tokens: Option<u32>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct TranscriptionConfig {
    pub model: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct TurnDetectionConfig {
    #[serde(rename = "type")]
    pub detection_type: String,
    pub threshold: f32,
    pub prefix_padding_ms: u32,
    pub silence_duration_ms: u32,
    pub interrupt_response: bool,
    pub create_response: bool,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ResponseConfig {
    pub modalities: Vec<String>,
    pub instructions: Option<String>,
    pub voice: Option<String>,
    pub output_audio_format: Option<String>,
    pub tools: Option<Vec<serde_json::Value>>,
    pub tool_choice: Option<String>,
    pub temperature: Option<f32>,
    pub max_output_tokens: Option<u32>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ConversationItem {
    pub id: Option<String>,
    #[serde(rename = "type")]
    pub item_type: String,
    pub status: Option<String>,
    pub role: String,
    pub content: Vec<ContentPart>,
}

#[derive(Serialize, Deserialize, Debug)]
#[serde(tag = "type")]
pub enum ContentPart {
    #[serde(rename = "input_text")]
    InputText { text: String },
    #[serde(rename = "input_audio")]
    InputAudio {
        audio: String,
        transcript: Option<String>,
    },
    #[serde(rename = "text")]
    Text { text: String },
    #[serde(rename = "audio")]
    Audio {
        audio: String,
        transcript: Option<String>,
    },
}

// Incoming message types from OpenAI
#[derive(Serialize, Deserialize, Debug)]
#[serde(tag = "type")]
pub enum OpenAIRealtimeResponse {
    #[serde(rename = "error")]
    Error { error: ErrorDetails },
    #[serde(rename = "response.created")]
    ResponseCreated { response: serde_json::Value },
    #[serde(rename = "session.created")]
    SessionCreated { session: serde_json::Value },
    #[serde(rename = "session.updated")]
    SessionUpdated { session: serde_json::Value },
    #[serde(rename = "conversation.item.created")]
    ConversationItemCreated { item: serde_json::Value },
    #[serde(rename = "conversation.item.truncated")]
    ConversationItemTruncated { item: serde_json::Value },
    #[serde(rename = "response.audio.delta")]
    ResponseAudioDelta {
        response_id: String,
        item_id: String,
        output_index: u32,
        content_index: u32,
        delta: String, // base64 encoded audio
    },
    #[serde(rename = "response.audio.done")]
    ResponseAudioDone {
        response_id: String,
        item_id: String,
        output_index: u32,
        content_index: u32,
    },
    #[serde(rename = "response.text.delta")]
    ResponseTextDelta {
        response_id: String,
        item_id: String,
        output_index: u32,
        content_index: u32,
        delta: String,
    },
    #[serde(rename = "response.audio_transcript.delta")]
    ResponseAudioTranscriptDelta {
        response_id: String,
        item_id: String,
        output_index: u32,
        content_index: u32,
        delta: String,
    },
    #[serde(rename = "response.done")]
    ResponseDone { response: serde_json::Value },
    #[serde(rename = "input_audio_buffer.speech_started")]
    InputAudioBufferSpeechStarted {
        audio_start_ms: u32,
        item_id: String,
    },
    #[serde(rename = "input_audio_buffer.speech_stopped")]
    InputAudioBufferSpeechStopped { audio_end_ms: u32, item_id: String },
    #[serde(other)]
    Other,
}

fn convert_pcm16_to_f32(bytes: &[u8]) -> Vec<f32> {
    let mut samples = Vec::with_capacity(bytes.len() / 2);

    for chunk in bytes.chunks_exact(2) {
        let pcm16_sample = i16::from_le_bytes([chunk[0], chunk[1]]);
        let f32_sample = pcm16_sample as f32 / 32767.0;
        samples.push(f32_sample);
    }

    samples
}

fn convert_f32_to_pcm16(samples: &[f32]) -> Vec<u8> {
    let mut pcm16_bytes = Vec::with_capacity(samples.len() * 2);

    for &sample in samples {
        // Clamp to [-1.0, 1.0] and convert to i16
        let clamped = sample.max(-1.0).min(1.0);
        let pcm16_sample = (clamped * 32767.0) as i16;
        pcm16_bytes.extend_from_slice(&pcm16_sample.to_le_bytes());
    }

    pcm16_bytes
}


async fn handle_client(fut: upgrade::UpgradeFut) -> Result<(), WebSocketError> {
    println!("WebSocket client connected, waiting for upgrade completion");
    let mut ws = fastwebsockets::FragmentCollector::new(fut.await?);
    println!("WebSocket connection established, waiting for first message");

    let frame = ws.read_frame().await?;
    println!("Received first frame, opcode: {:?}, payload size: {}", frame.opcode, frame.payload.len());
    
    if frame.opcode != OpCode::Text {
        println!("ERROR: Expected text frame, got {:?}", frame.opcode);
        // Send proper close for protocol error
        ws.write_frame(Frame::close(1002, b"Protocol error")).await?;
        return Err(WebSocketError::InvalidConnectionHeader);
    }
    
    println!("Parsing message as OpenAIRealtimeMessage");
    let data: OpenAIRealtimeMessage = match serde_json::from_slice(&frame.payload) {
        Ok(msg) => {
            println!("Successfully parsed message");
            msg
        },
        Err(e) => {
            println!("ERROR: Failed to parse message: {}", e);
            println!("Raw payload: {}", String::from_utf8_lossy(&frame.payload));
            // Unsupported/invalid initial data
            ws.write_frame(Frame::close(1003, b"Unsupported data")).await?;
            return Err(WebSocketError::InvalidConnectionHeader);
        }
    };
    
    let OpenAIRealtimeMessage::SessionUpdate { session } = data else {
        println!("ERROR: Expected SessionUpdate, got different message type");
        ws.write_frame(Frame::close(1003, b"Unsupported data")).await?;
        return Err(WebSocketError::InvalidConnectionHeader);
    };
    println!("Received SessionUpdate from client");

    let input_audio_transcription = session
        .input_audio_transcription
        .as_ref()
        .map_or("whisper".to_string(), |t| {
            println!("Client requested transcription model: {}", t.model);
            t.model.clone()
        });
    let llm = session.model.clone();
    println!("Session config - Transcription: {}, LLM: {}", input_audio_transcription, llm);
    
    // Accept any model name from moly, but log what we're actually using
    println!("Client requested model: {}", llm);
    if llm.contains("Qwen") || llm.contains("GGUF") {
        println!("Note: Client requested a Qwen/GGUF model, will use whatever is configured in the template");
    }
    
    // Prepare session response but DON'T send yet - wait until maas-client is ready
    let session_response = serde_json::json!({
        "id": format!("session_wserver"),
        "object": "realtime.session",
        "model": session.model.clone(),
        "modalities": session.modalities.clone(),
        "instructions": session.instructions.clone(),
        "voice": session.voice.clone(),
        "input_audio_format": session.input_audio_format.clone(),
        "output_audio_format": session.output_audio_format.clone(),
        "input_audio_transcription": session.input_audio_transcription.clone(),
        "turn_detection": session.turn_detection.clone(),
        "tools": session.tools.clone(),
        "tool_choice": session.tool_choice.clone(),
        "temperature": session.temperature,
        "max_response_output_tokens": session.max_response_output_tokens,
    });
    
    println!("Session response prepared, but will wait to send until maas-client is ready...");
    
    // NOTE: Dynamic nodes are now connected at server startup, not per-client
    // The wserver and maas-client nodes are initialized in main() when --name is provided
    // This avoids reconnecting for each client session
    
    // For now, we still need to create a Dora node connection per client
    // Use the shared node connection from main()
    println!("Using shared Dora node connection for client session...");
    
    let node_arc = match DORA_NODE.get() {
        Some(n) => n.clone(),
        None => {
            eprintln!("❌ Dora node not initialized. Make sure to run with --name argument");
            let _ = ws.write_frame(Frame::text(Payload::Borrowed(r#"{
                "type": "error",
                "error": {
                    "message": "Server not connected to dataflow. Please restart the server with --name argument.",
                    "type": "server_error",
                    "code": "dataflow_not_connected"
                }
            }"#.as_bytes()))).await;
            return Ok(());
        }
    };
    
    let events_arc = match DORA_EVENTS.get() {
        Some(e) => e.clone(),
        None => {
            eprintln!("❌ Dora events not initialized");
            return Ok(());
        }
    };
    
    // Optionally spawn a dynamic maas-client. When using a static maas-client in the dataflow,
    // set SPAWN_MAAS=0 (or "false") to skip spawning here and reuse the existing node.
    let spawn_maas = std::env::var("SPAWN_MAAS")
        .map(|v| matches!(v.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(true);

    if spawn_maas {
        // Kill existing maas-client if any and spawn a new one with updated config
        if let Some(pid_arc) = MAAS_PID.get() {
        let mut pid_guard = pid_arc.lock().await;
        if let Some(pid) = *pid_guard {
            println!("Killing existing maas-client with PID: {}", pid);
            // Try to kill the process
            let _ = std::process::Command::new("kill")
                .arg("-9")
                .arg(pid.to_string())
                .output();
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
        }
        
        // Spawn new maas-client with potentially updated config
        println!("Spawning new maas-client for this session...");
        // Use relative path or get from environment variable
        let config_path = std::env::var("MAAS_CONFIG_PATH")
            .unwrap_or_else(|_| "maas_mcp_browser_config.toml".to_string());
        
        match tokio::process::Command::new("dora-maas-client")
            .arg("--name")
            .arg("maas-client")
            .env("MAAS_CONFIG_PATH", &config_path)
            .spawn() {
            Ok(mut child) => {
                if let Some(pid) = child.id() {
                    println!("✅ New maas-client spawned with PID: {}", pid);
                    println!("   Using config: {}", config_path);
                    *pid_guard = Some(pid);
                    
                    // Monitor the process in the background
                    tokio::spawn(async move {
                        match child.wait().await {
                            Ok(status) => {
                                if !status.success() {
                                    eprintln!("⚠️ maas-client exited with status: {:?}", status);
                                }
                            }
                            Err(e) => {
                                eprintln!("⚠️ Error waiting for maas-client: {}", e);
                            }
                        }
                    });
                }
            }
            Err(e) => {
                eprintln!("⚠️ Failed to spawn maas-client from PATH: {}", e);
                eprintln!("   Falling back to 'cargo run -p dora-maas-client' (dev flow)");
                match tokio::process::Command::new("cargo")
                    .arg("run")
                    .arg("-p")
                    .arg("dora-maas-client")
                    .arg("--")
                    .arg("--name")
                    .arg("maas-client")
                    .env("MAAS_CONFIG_PATH", &config_path)
                    .spawn() {
                    Ok(mut child) => {
                        if let Some(pid) = child.id() {
                            println!("✅ Fallback cargo run: maas-client PID: {}", pid);
                            println!("   Using config: {}", config_path);
                            *pid_guard = Some(pid);
                            tokio::spawn(async move {
                                match child.wait().await {
                                    Ok(status) => {
                                        if !status.success() {
                                            eprintln!("⚠️ maas-client (cargo run) exited with status: {:?}", status);
                                        }
                                    }
                                    Err(e) => {
                                        eprintln!("⚠️ Error waiting for maas-client (cargo run): {}", e);
                                    }
                                }
                            });
                        }
                    }
                    Err(e2) => {
                        eprintln!("❌ Failed to spawn maas-client via cargo run as well: {}", e2);
                    }
                }
            }
        }
        
            // Wait for maas-client to be ready before sending session acknowledgments
            println!("⏳ Waiting 10 seconds for maas-client to connect to dataflow...");
            tokio::time::sleep(tokio::time::Duration::from_secs(10)).await;
            println!("✅ maas-client should now be ready");
        }
    } else {
        println!("SPAWN_MAAS disabled; using existing static maas-client in dataflow");
    }
    
    // NOW send session acknowledgments after maas-client is ready
    println!("Sending session acknowledgments to client now that maas-client is ready...");
    
    let serialized_data = OpenAIRealtimeResponse::SessionCreated {
        session: session_response.clone(),
    };
    let payload =
        Payload::Bytes(Bytes::from(serde_json::to_string(&serialized_data).unwrap()).into());
    let frame = Frame::text(payload);
    println!("Sending session.created acknowledgment to client");
    ws.write_frame(frame).await?;
    
    // Also send session.updated to confirm the session update was processed
    let serialized_updated = OpenAIRealtimeResponse::SessionUpdated {
        session: session_response,
    };
    let payload_updated =
        Payload::Bytes(Bytes::from(serde_json::to_string(&serialized_updated).unwrap()).into());
    let frame_updated = Frame::text(payload_updated);
    println!("Sending session.updated acknowledgment to client");
    ws.write_frame(frame_updated).await?;
    
    let mut node = node_arc.lock().await;
    let mut events = events_arc.lock().await;
    
    // Create resampler with fixed buffer size for microphone input
    const DOWNSAMPLE_CHUNK_SIZE: usize = 4800; // 200ms at 24kHz
    
    let resampler_params = SincInterpolationParameters {
        sinc_len: 256,          // High quality
        f_cutoff: 0.95,
        interpolation: SincInterpolationType::Cubic,
        oversampling_factor: 256,
        window: WindowFunction::BlackmanHarris2,
    };
    
    // Downsampler for microphone input (24kHz -> 16kHz)
    let mut downsampler = SincFixedIn::<f32>::new(
        16000.0 / 24000.0,  // Resample ratio (2/3)
        2.0,                // Max delay
        resampler_params,
        DOWNSAMPLE_CHUNK_SIZE,  // Fixed input size
        1,                  // 1 channel (mono)
    ).expect("Failed to create downsampler");
    
    let mut audio_buffer = Vec::new(); // Buffer for microphone audio
    // Segment counting is now handled via metadata from primespeech
    
    println!("🚀 Starting main event loop with fixed-size resampler");
    println!("📊 Pipeline: WebSocket → ASR → MaaS → Text-Segmenter → TTS → Audio → WebSocket");
    println!("👂 Listening for audio input and text output from dataflow nodes...");
    println!("" );
    
    // Wait for client to send greeting via ResponseCreate message
    println!("⏳ Waiting for client to send greeting via response.create message...");
    
    let mut audio_chunks_received = 0;
    let mut text_chunks_sent = 0;
    let mut last_activity = std::time::Instant::now();
    let mut should_send_completion = false; // Track if we need to send completion events after audio
    let mut response_created_sent = false; // Ensure response.created is sent once per turn
    let mut response_active = false; // Only emit deltas while a response is active
    // Track if we've replied to a Close frame
    let mut close_replied = false;
    // Deduplicate greeting instructions to avoid repeated forwards
    let mut last_greeting: Option<String> = None;
    let mut last_greet_time: Option<std::time::Instant> = None;
    loop {
        let event_fut = events.recv_async().map(Either::Left);
        let frame_fut = ws.read_frame().map(Either::Right);
        let event_stream = (event_fut, frame_fut).race();
        let frame = match event_stream.await {
            future::Either::Left(Some(ev)) => {
                let frame = match ev {
                    dora_node_api::Event::Input {
                        id,
                        metadata,
                        data,
                    } => {
                        let now = std::time::Instant::now();
                        let time_since_last = now.duration_since(last_activity).as_millis();
                        last_activity = now;
                        
                        if data.data_type() == &DataType::Utf8 {
                            let data = data.as_string::<i32>();
                            let str = data.value(0);
                            text_chunks_sent += 1;
                            
                            // Determine the source node and log appropriately with full pipeline context
                            if id.contains("segment_complete") {
                                // PrimeSpeech completion or error
                                if str == "error" {
                                    // Try to surface error details from metadata
                                    let mut err = String::from("unknown");
                                    let mut stage = String::from("unknown");
                                    if let Some(param) = metadata.parameters.get("error") {
                                        if let dora_node_api::Parameter::String(s) = param { err = s.clone(); }
                                    }
                                    if let Some(param) = metadata.parameters.get("error_stage") {
                                        if let dora_node_api::Parameter::String(s) = param { stage = s.clone(); }
                                    }
                                    println!("┌─ [{}ms] ❌ TTS ERROR", time_since_last);
                                    println!("│  Node: {} → WebSocket", id);
                                    println!("│  Stage: {}", stage);
                                    println!("│  Error: {}", err);
                                    if let Some(param) = metadata.parameters.get("segment_index") {
                                        if let dora_node_api::Parameter::Integer(i) = param { println!("│  Segment: {}", i); }
                                    }
                                    println!("└─ ⚠️  Forwarding 'error' to client for visibility");
                                } else {
                                    let mut remaining: i64 = -1;
                                    if let Some(param) = metadata.parameters.get("segments_remaining") {
                                        if let dora_node_api::Parameter::Integer(i) = param { remaining = *i; }
                                    }
                                    println!("┌─ [{}ms] ✅ TTS SEGMENT COMPLETE", time_since_last);
                                    println!("│  Node: {} → WebSocket", id);
                                    println!("│  Status: '{}'", str);
                                    println!("│  Segments remaining: {}", remaining);
                                    println!("└─ 📤 Notifying client of completion");
                                }
                            } else if id.contains("log") {
                                // Log channel (e.g., from PrimeSpeech)
                                println!("┌─ [{}ms] 🪵 NODE LOG", time_since_last);
                                println!("│  Source: {}", id);
                                println!("│  Message: {}", str);
                                println!("└─ ▶️  Not forwarding node logs to client");
                                // Skip forwarding of debug logs to client to avoid protocol noise
                                continue;
                            } else if id.contains("transcription") {
                                println!("┌─ [{}ms] 🎙️  ASR OUTPUT", time_since_last);
                                println!("│  Node: {} → WebSocket", id);
                                println!("│  Text: '{}'", str.chars().take(100).collect::<String>());
                                println!("│  Stats: Chunk #{}, {} chars", text_chunks_sent, str.len());
                                println!("└─ 📤 Forwarding to client as transcription delta");
                            } else if id.contains("text") && (id.contains("maas") || id.contains("qwen")) {
                                println!("┌─ [{}ms] 🤖 LLM OUTPUT", time_since_last);
                                println!("│  Node: {} → WebSocket", id);
                                println!("│  Text: '{}'", str.chars().take(100).collect::<String>());
                                println!("│  Stats: Chunk #{}, {} chars", text_chunks_sent, str.len());
                                println!("└─ 📤 Forwarding to client as text delta");
                            } else {
                                println!("┌─ [{}ms] 📝 TEXT OUTPUT", time_since_last);
                                println!("│  Node: {} → WebSocket", id);
                                println!("│  Text: '{}'", str.chars().take(100).collect::<String>());
                                println!("│  Stats: Chunk #{}, {} chars", text_chunks_sent, str.len());
                                println!("└─ 📤 Forwarding to client");
                            }
                            
                            // Ensure a response is active before sending any deltas
                            if !response_active {
                                let created = OpenAIRealtimeResponse::ResponseCreated {
                                    response: serde_json::json!({
                                        "id": "123",
                                        "status": "in_progress",
                                        "output": []
                                    }),
                                };
                                let created_frame = Frame::text(Payload::Bytes(
                                    Bytes::from(serde_json::to_string(&created).unwrap()).into(),
                                ));
                                ws.write_frame(created_frame).await?;
                                println!("✅ Sent response.created (id=123) before transcript/text delta");
                                response_created_sent = true;
                                response_active = true;
                            }

                            // Route: ASR transcription -> transcript delta; LLM text -> text delta
                            let serialized_data = if id.contains("transcription") {
                                OpenAIRealtimeResponse::ResponseAudioTranscriptDelta {
                                    response_id: "123".to_string(),
                                    item_id: "123".to_string(),
                                    output_index: 123,
                                    content_index: 123,
                                    delta: str.to_string(),
                                }
                            } else {
                                OpenAIRealtimeResponse::ResponseTextDelta {
                                    response_id: "123".to_string(),
                                    item_id: "123".to_string(),
                                    output_index: 123,
                                    content_index: 123,
                                    delta: str.to_string(),
                                }
                            };

                            let frame = Frame::text(Payload::Bytes(
                                Bytes::from(serde_json::to_string(&serialized_data).unwrap()).into(),
                            ));
                            frame
                        } else if id.contains("audio") {
                            audio_chunks_received += 1;
                            
                            // Extract segments_remaining from metadata
                            let segments_remaining = if let Some(param) = metadata.parameters.get("segments_remaining") {
                                match param {
                                    dora_node_api::Parameter::Integer(i) => *i as u32,
                                    _ => 999
                                }
                            } else {
                                999
                            }; // Default to high number if not present
                            
                            // Log audio processing with enhanced detail
                            if id.contains("primespeech") {
                                println!("┌─ [{}ms] 🔊 TTS OUTPUT", time_since_last);
                                println!("│  Node: {} → WebSocket", id);
                                println!("│  Audio: {} samples, {} bytes", data.len(), data.get_array_memory_size());
                                println!("│  Stats: Chunk #{}, segments_remaining: {}", audio_chunks_received, segments_remaining);
                                println!("└─ 📤 Forwarding to client as audio data");
                            } else if id.contains("audio-player") {
                                println!("┌─ [{}ms] 🎵 AUDIO PLAYBACK", time_since_last);
                                println!("│  Node: {} → WebSocket", id);
                                println!("│  Audio: {} samples", data.len());
                                println!("│  Stats: Chunk #{}, segments_remaining: {}", audio_chunks_received, segments_remaining);
                                println!("└─ 📤 Forwarding to client");
                            } else {
                                println!("┌─ [{}ms] 🎵 AUDIO OUTPUT", time_since_last);
                                println!("│  Node: {} → WebSocket", id);
                                println!("│  Audio: {} samples", data.len());
                                println!("│  Stats: Chunk #{}, segments_remaining: {}", audio_chunks_received, segments_remaining);
                                println!("└─ 📤 Forwarding to client");
                            }
                            
                            // Handle audio data - it might be a list/array
                            let audio_data = if let Ok(vec_data) = into_vec::<f32>(&data) {
                                println!("   ✓ Extracted {} audio samples using into_vec", vec_data.len());
                                vec_data
                            } else {
                                // Try different array types
                                if let Some(array) = data.as_any().downcast_ref::<dora_node_api::arrow::array::Float32Array>() {
                                    println!("   ✓ Converting from Float32Array ({} samples)", array.len());
                                    let mut vec_data = Vec::with_capacity(array.len());
                                    for i in 0..array.len() {
                                        if array.is_valid(i) {
                                            vec_data.push(array.value(i));
                                        }
                                    }
                                    vec_data
                                } else if let Some(list_array) = data.as_any().downcast_ref::<dora_node_api::arrow::array::ListArray>() {
                                    // println!("Converting from ListArray with {} elements", list_array.len());
                                    // For PrimeSpeech: pa.array([audio_array]) creates a list with one element
                                    if list_array.len() > 0 {
                                        // Get the first (and usually only) element
                                        let values = list_array.value(0);
                                        // println!("ListArray element type: {:?}", values.data_type());
                                        
                                        if let Some(float_array) = values.as_any().downcast_ref::<dora_node_api::arrow::array::Float32Array>() {
                                            // println!("Extracting {} float32 samples from ListArray", float_array.len());
                                            let mut vec_data = Vec::with_capacity(float_array.len());
                                            for i in 0..float_array.len() {
                                                if float_array.is_valid(i) {
                                                    vec_data.push(float_array.value(i));
                                                }
                                            }
                                            vec_data
                                        } else {
                                            println!("ERROR: ListArray element is not Float32Array, it's: {:?}", values.data_type());
                                            continue;
                                        }
                                    } else {
                                        println!("ERROR: Empty ListArray");
                                        continue;
                                    }
                                } else {
                                    println!("ERROR: Unknown array type, cannot downcast");
                                    continue;
                                }
                            };
                            
                            // For TTS, process immediately without buffering for low latency
                            // Create a resampler for this chunk (use source sample_rate from metadata if present)
                            let params = SincInterpolationParameters {
                                sinc_len: 64,  // Lower for faster processing
                                f_cutoff: 0.95,
                                interpolation: SincInterpolationType::Linear,
                                oversampling_factor: 128,
                                window: WindowFunction::Blackman,
                            };
                            // Determine source sample rate (fallback to 32000) and resample to 24000
                            let src_rate: f64 = if let Some(param) = metadata.parameters.get("sample_rate") {
                                match param { dora_node_api::Parameter::Integer(i) => (*i as f64).max(1.0), _ => 32000.0 }
                            } else { 32000.0 };
                            let dst_rate: f64 = 24000.0;
                            let ratio = (dst_rate / src_rate).max(1e-6);
                            println!("   ℹ️  Resampling {} -> {} (ratio {:.5})", src_rate as i64, dst_rate as i64, ratio);

                            let mut resampler = SincFixedIn::<f32>::new(
                                ratio,
                                2.0,
                                params,
                                audio_data.len().max(1),   // Avoid zero-sized buffer
                                1,
                            ).expect("Failed to create TTS resampler");

                            let input = vec![audio_data];
                            let output = resampler.process(&input, None).expect("TTS resampling failed");
                            let resampled = output[0].clone();
                            println!("   ✓ Resampled {} → {} samples", input[0].len(), resampled.len());

                            let data = convert_f32_to_pcm16(&resampled);
                            println!("   ✓ Encoded PCM16 bytes: {}", data.len());

                            // Ensure we notify the client a response was created before first delta
                            if !response_created_sent {
                                let created = OpenAIRealtimeResponse::ResponseCreated {
                                    response: serde_json::json!({
                                        "id": "123",
                                        "status": "in_progress",
                                        "output": []
                                    }),
                                };
                                let created_frame = Frame::text(Payload::Bytes(
                                    Bytes::from(serde_json::to_string(&created).unwrap()).into(),
                                ));
                                ws.write_frame(created_frame).await?;
                                println!("✅ Sent response.created (id=123)");
                                response_created_sent = true;
                                response_active = true;
                            }
                            let serialized_data = OpenAIRealtimeResponse::ResponseAudioDelta {
                                response_id: "123".to_string(),
                                item_id: "123".to_string(),
                                output_index: 123,
                                content_index: 123,
                                delta: general_purpose::STANDARD.encode(data),
                            };

                            let frame = Frame::text(Payload::Bytes(
                                Bytes::from(serde_json::to_string(&serialized_data).unwrap())
                                    .into(),
                            ));
                            
                            // Check if this is the last segment and set flag
                            if segments_remaining == 0 {
                                println!("🎯 Last segment detected (segments_remaining=0), will send completion events AFTER audio");
                                should_send_completion = true;
                            }
                            
                            // Return the audio frame to be sent first
                            frame
                        } else if id.contains("speech_started") {
                            let serialized_data =
                                OpenAIRealtimeResponse::InputAudioBufferSpeechStarted {
                                    audio_start_ms: 123,
                                    item_id: "123".to_string(),
                                };

                            let frame = Frame::text(Payload::Bytes(
                                Bytes::from(serde_json::to_string(&serialized_data).unwrap())
                                    .into(),
                            ));
                            frame
                        } else if id.contains("question_ended") {
                            println!("❓ Question ended detected - complete sentence, triggering LLM response");
                            
                            // Send speech stopped event to indicate a complete question
                            let speech_stopped = OpenAIRealtimeResponse::InputAudioBufferSpeechStopped {
                                audio_end_ms: 123,
                                item_id: "123".to_string(),
                            };
                            let frame = Frame::text(Payload::Bytes(
                                Bytes::from(serde_json::to_string(&speech_stopped).unwrap()).into(),
                            ));
                            
                            // Queue additional events to send after this frame
                            // When using server_vad, we need to:
                            // 1. Commit the audio buffer 
                            // 2. Create a response
                            
                            // Store the frame to return, but also queue commit and response
                            let commit_msg = serde_json::json!({
                                "type": "input_audio_buffer.committed",
                                "item_id": "123",
                                "audio": ""  // Empty audio since we already sent it
                            });
                            let commit_frame = Frame::text(Payload::Bytes(
                                Bytes::from(serde_json::to_string(&commit_msg).unwrap()).into(),
                            ));
                            
                            // Create response to trigger LLM
                            let create_response = serde_json::json!({
                                "type": "response.create",
                                "response": {
                                    "modalities": ["text", "audio"],
                                    "instructions": null,
                                    "voice": null,
                                    "output_audio_format": "pcm16",
                                    "tools": [],
                                    "tool_choice": "none",
                                    "temperature": 0.8,
                                    "max_output_tokens": 4096
                                }
                            });
                            let response_frame = Frame::text(Payload::Bytes(
                                Bytes::from(serde_json::to_string(&create_response).unwrap()).into(),
                            ));
                            
                            // Send all three events
                            // Note: We can only return one frame here, so we'll need to handle this differently
                            // For now, just send the speech_stopped event
                            frame
                        } else {
                            // Ignore other inputs (e.g., question_ended, is_speaking, speech_probability, log)
                            continue;
                        }
                    }
                    dora_node_api::Event::Error(_) => {
                        // Keep the WebSocket open on upstream errors; just skip this event
                        continue;
                    }
                    dora_node_api::Event::InputClosed { id } => {
                        // Do NOT close the WebSocket when a single input closes (e.g., text).
                        // This event only indicates no more items for that input; the session continues.
                        println!("ℹ️  Dora input closed: {:?}", id);
                        continue;
                    }
                    _ => {
                        // Ignore other event types to keep the connection alive
                        continue;
                    },
                };
                Some(frame)
            }
            future::Either::Left(None) => break,
            future::Either::Right(Ok(frame)) => {
                // println!("Received WebSocket frame, opcode: {:?}, payload size: {}", frame.opcode, frame.payload.len());
                match frame.opcode {
                    OpCode::Close => {
                        // Echo close and break the loop
                        if !close_replied {
                            ws.write_frame(Frame::close(1000, b"Normal closure")).await?;
                            close_replied = true;
                        }
                        break
                    },
                    OpCode::Ping => {
                        // Respond to ping with pong to keep the connection alive
                        let pong = Frame::pong(frame.payload);
                        ws.write_frame(pong).await?;
                        continue;
                    }
                    OpCode::Pong => {
                        // Ignore
                        continue;
                    }
                    OpCode::Text | OpCode::Binary => {
                        // Parse client JSON safely; ignore unknown or malformed messages
                        let parsed: Result<OpenAIRealtimeMessage, _> =
                            serde_json::from_slice(&frame.payload);
                        let data = match parsed {
                            Ok(d) => d,
                            Err(e) => {
                                println!(
                                    "⚠️  Ignoring malformed client message ({} bytes): {}",
                                    frame.payload.len(), e
                                );
                                // Keep the connection open; move to next iteration
                                continue;
                            }
                        };
                        // println!("Parsed WebSocket message type: {:?}", std::mem::discriminant(&data));

                        match data {
                            OpenAIRealtimeMessage::InputAudioBufferAppend { audio } => {
                                // println!("📡 Received audio buffer from client, base64 length: {}", audio.len());
                                let f32_data = audio;
                                // Decode base64 encoded audio data
                                let f32_data = f32_data.trim();
                                if f32_data.is_empty() {
                                    println!("⚠️ Empty audio buffer received, skipping");
                                    continue;
                                }

                                match general_purpose::STANDARD.decode(f32_data) {
                                    Ok(decoded_data) => {
                                        // println!("Decoded {} bytes of PCM16 audio", decoded_data.len());
                                        let f32_data = convert_pcm16_to_f32(&decoded_data);
                                        // println!("Converted to {} f32 samples", f32_data.len());
                                        
                                        // Add to buffer
                                        audio_buffer.extend_from_slice(&f32_data);
                                        
                                        // Process buffer in fixed-size chunks
                                        while audio_buffer.len() >= DOWNSAMPLE_CHUNK_SIZE {
                                            // Take exactly DOWNSAMPLE_CHUNK_SIZE samples
                                            let chunk: Vec<f32> = audio_buffer.drain(..DOWNSAMPLE_CHUNK_SIZE).collect();
                                            
                                            // Resample using the pre-created downsampler
                                            let input = vec![chunk];
                                            let output = downsampler.process(&input, None).expect("Resampling failed");
                                            let f32_data = output[0].clone();
                                            
                                            let mut parameter = MetadataParameters::default();
                                            parameter.insert(
                                                "sample_rate".to_string(),
                                                dora_node_api::Parameter::Integer(16000),
                                            );
                                            // println!("Sending {} audio samples to speech-monitor", f32_data.len());
                                            match node.send_output(
                                                DataId::from("audio".to_string()),
                                                parameter,
                                                f32_data.to_vec().into_arrow(),  // Create a fresh vector copy
                                            ) {
                                                Ok(_) => {}, // println!("Successfully sent audio to speech-monitor"),
                                                Err(e) => println!("ERROR sending audio: {:?}", e),
                                            }
                                        }
                                    }
                                    Err(e) => {
                                        println!("ERROR: Failed to decode base64 audio: {:?}", e);
                                        println!("Base64 string length: {}, first 100 chars: {}", 
                                                f32_data.len(), 
                                                &f32_data[..f32_data.len().min(100)]);
                                    }
                                }
                            }
                            OpenAIRealtimeMessage::InputAudioBufferCommit => {
                                println!("✅ Received InputAudioBufferCommit from client");
                                // Don't break - just continue processing
                                // This allows continuous audio streaming
                                continue;
                            }
                            OpenAIRealtimeMessage::ResponseCreate { response } => {
                                println!("📨 Received ResponseCreate from client with instructions");
                                if let Some(text) = response.instructions {
                                    // Throttle duplicate greetings: ignore if same as the last within 3s
                                    let now = std::time::Instant::now();
                                    let is_dup = last_greeting.as_ref().map(|g| g == &text).unwrap_or(false)
                                        && last_greet_time.map(|t| now.duration_since(t).as_millis() < 3000).unwrap_or(false);
                                    if is_dup {
                                        println!("↩️  Ignoring duplicate greeting within 3s window");
                                    } else {
                                        println!("🎯 Forwarding greeting instructions to maas-client: {}", text);
                                        match node.send_output(
                                            DataId::from("text".to_string()),
                                            Default::default(),
                                            text.clone().into_arrow(),
                                        ) {
                                            Ok(_) => {
                                                last_greeting = Some(text);
                                                last_greet_time = Some(now);
                                                println!("✅ Successfully sent greeting to maas-client");
                                                println!("⏳ Waiting for LLM response and TTS audio...");
                                            }
                                            Err(e) => {
                                                eprintln!("⚠️ Failed to send greeting to maas-client: {:?}", e);
                                                eprintln!("   This might happen if maas-client isn't fully connected yet");
                                            }
                                        }
                                    }
                                }
                            }
                            OpenAIRealtimeMessage::Other => {
                                // Unknown/unsupported client message type; skip
                                continue;
                            }
                            _ => {}
                        }
                    }
                    _ => {
                        // Ignore other client message variants; keep the connection open
                        continue;
                    },
                }
                None
            }
            future::Either::Right(Err(_)) => break,
        };
        if let Some(frame) = frame {
            // Check if this is a question_ended event that needs additional frames
            let is_question_ended = if let Frame { payload: Payload::Bytes(ref data), .. } = frame {
                let text = String::from_utf8_lossy(data);
                text.contains("input_audio_buffer.speech_stopped")
            } else {
                false
            };
            
            ws.write_frame(frame).await?;
            
            // If question ended, do NOT send client-origin events back to the client.
            // We already forward ASR text to the MaaS client, which triggers the LLM.
            // Sending `input_audio_buffer.committed` or `response.create` from server→client
            // is invalid for the OpenAI Realtime protocol and can cause disconnects.
            if is_question_ended {
                println!("ℹ️  Question ended detected; relying on server-side LLM trigger (no client-origin events sent)");
            }
            
            // Send completion events immediately after audio frame if this was the last segment
            if should_send_completion {
                println!("📤 Sending completion events after last audio segment");
                
                // Send response.audio.done
                let audio_done = OpenAIRealtimeResponse::ResponseAudioDone {
                    response_id: "123".to_string(),
                    item_id: "123".to_string(),
                    output_index: 123,
                    content_index: 123,
                };
                let audio_done_frame = Frame::text(Payload::Bytes(
                    Bytes::from(serde_json::to_string(&audio_done).unwrap()).into(),
                ));
                ws.write_frame(audio_done_frame).await?;
                println!("✅ Sent response.audio.done");
                
                // Send response.done  
                let response_done = OpenAIRealtimeResponse::ResponseDone {
                    response: serde_json::json!({
                        "id": "123",
                        "status": "completed",
                        "status_details": null,
                        "output": [],
                        "usage": {
                            "total_tokens": 0,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "input_token_details": {
                                "cached_tokens": 0,
                                "text_tokens": 0,
                                "audio_tokens": 0
                            },
                            "output_token_details": {
                                "cached_tokens": 0,
                                "text_tokens": 0,
                                "audio_tokens": 0
                            }
                        }
                    }),
                };
                let response_done_frame = Frame::text(Payload::Bytes(
                    Bytes::from(serde_json::to_string(&response_done).unwrap()).into(),
                ));
                ws.write_frame(response_done_frame).await?;
                println!("✅ Sent response.done - conversation complete");
                
                // Reset flags; mark response as closed to suppress late deltas
                should_send_completion = false;
                response_created_sent = false;
                response_active = false;
            }
        }
    }
    
    // Connection closed - send a proper close if we haven't yet
    if !close_replied {
        let _ = ws.write_frame(Frame::close(1000, b"Normal closure")).await;
    }
    println!("🔌 WebSocket client disconnected");

    Ok(())
}
async fn server_upgrade(
    mut req: Request<Incoming>,
) -> Result<Response<Empty<Bytes>>, WebSocketError> {
    println!("WebSocket upgrade request received");
    println!("  Method: {:?}", req.method());
    println!("  URI: {:?}", req.uri());
    println!("  Headers:");
    for (name, value) in req.headers() {
        println!("    {}: {:?}", name, value);
    }
    
    let (response, fut) = upgrade::upgrade(&mut req)?;
    println!("WebSocket upgrade successful");

    tokio::task::spawn(async move {
        if let Err(e) = tokio::task::unconstrained(handle_client(fut)).await {
            eprintln!("Error in websocket connection: {}", e);
        }
    });

    Ok(response)
}

fn main() -> Result<(), WebSocketError> {
    let rt = tokio::runtime::Builder::new_multi_thread()
        .enable_io()
        .enable_time()
        .build()
        .unwrap();

    rt.block_on(async move {
        // Static dataflow should be started separately via CLI
        // Example: dora start whisper-template-metal.yml --name static-dataflow --detach
        println!("WebSocket server starting...");
        println!("Note: Static dataflow should be started separately via CLI");
        
        // Parse command line arguments to check for --name
        let args: Vec<String> = std::env::args().collect();
        let mut node_name: Option<String> = None;
        
        // Look for --name argument
        for i in 0..args.len() {
            if args[i] == "--name" && i + 1 < args.len() {
                node_name = Some(args[i + 1].clone());
                break;
            }
        }
        
        // // Automatic static dataflow starting (COMMENTED OUT - requires manual start)
        // // Get the absolute path to the dataflow file
        // let dataflow_path = if let Ok(path) = std::env::var("DATAFLOW_PATH") {
        //     path
        // } else {
        //     // Try to find the dataflow file relative to the project root
        //     let possible_paths = vec![
        //         "whisper-template-metal.yml",
        //         "examples/chatbot-openai-0905/whisper-template-metal.yml",
        //         "../examples/chatbot-openai-0905/whisper-template-metal.yml",
        //         "../../examples/chatbot-openai-0905/whisper-template-metal.yml",
        //     ];
        //     
        //     let mut found_path = None;
        //     for path in possible_paths {
        //         if std::path::Path::new(path).exists() {
        //             found_path = Some(path.to_string());
        //             break;
        //         }
        //     }
        //     
        //     found_path.unwrap_or_else(|| {
        //         eprintln!("WARNING: Could not find whisper-template-metal.yml");
        //         eprintln!("Please set DATAFLOW_PATH environment variable or run from the correct directory");
        //         "whisper-template-metal.yml".to_string()
        //     })
        // };
        // 
        // // Check if any dataflow is already running
        // let list_output = Command::new("dora")
        //     .arg("list")
        //     .output()
        //     .await
        //     .expect("Failed to execute dora list command");
        // 
        // let list_str = String::from_utf8_lossy(&list_output.stdout);
        // // Check if output contains a UUID (indicates a dataflow is running)
        // // The format is: UUID  Name  Status
        // let has_running_dataflow = list_str.lines()
        //     .skip(1) // Skip header
        //     .any(|line| !line.trim().is_empty());
        //     
        // if !has_running_dataflow {
        //     println!("Starting dataflow with persistent nodes...");
        //     
        //     let output = Command::new("dora")
        //         .arg("start")
        //         .arg(&dataflow_path)
        //         .arg("--detach")
        //         .output()
        //         .await
        //         .expect("Failed to execute dora start command");
        //     
        //     if !output.status.success() {
        //         eprintln!("Failed to start dataflow: {}", String::from_utf8_lossy(&output.stderr));
        //         return Err(WebSocketError::InvalidConnectionHeader);
        //     }
        //     
        //     println!("✅ Dataflow started successfully");
        //     
        //     // Wait for nodes to initialize
        //     println!("Waiting for nodes to initialize...");
        //     tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
        // } else {
        //     println!("✅ Dataflow already running");
        // }
        
        // Connect to dataflow as dynamic node if --name is provided
        if let Some(name) = &node_name {
            println!("Connecting to dataflow as dynamic node: {}", name);
            
            // Try to connect to dataflow
            match DoraNode::init_from_node_id(NodeId::from(name.clone())) {
                Ok((node, events)) => {
                    println!("✅ Successfully connected to dataflow as '{}'", name);
                    
                    // Store the node and events globally for sharing with WebSocket clients
                    DORA_NODE.set(Arc::new(Mutex::new(node))).unwrap_or_else(|_| panic!("Failed to set DORA_NODE"));
                    DORA_EVENTS.set(Arc::new(Mutex::new(events))).unwrap_or_else(|_| panic!("Failed to set DORA_EVENTS"));
                    
                    // Initialize MAAS_PID storage (will be set when client connects)
                    MAAS_PID.set(Arc::new(Mutex::new(None))).unwrap_or_else(|_| panic!("Failed to set MAAS_PID"));
                    
                    println!("✅ Dora node and events stored globally");
                    println!("⏳ Waiting for WebSocket client to connect before spawning maas-client...");
                }
                Err(e) => {
                    eprintln!("❌ Failed to connect to dataflow as '{}': {:?}", name, e);
                    eprintln!("Make sure the dataflow contains the node '{}'", name);
                    return Err(WebSocketError::InvalidConnectionHeader);
                }
            }
        } else {
            println!("Running in standalone mode (no --name argument provided)");
            println!("To connect as dynamic node, run with: --name wserver");
        }
        
        let port = std::env::var("PORT").unwrap_or_else(|_| "8123".to_string());
        let host = std::env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let addr = format!("{}:{}", host, port);
        let listener = TcpListener::bind(&addr).await?;
        println!("WebSocket server ready, listening on {}", addr);
        
        loop {
            let (stream, _) = listener.accept().await?;
            println!("Client connected");
            
            tokio::spawn(async move {
                let io = hyper_util::rt::TokioIo::new(stream);
                let conn_fut = http1::Builder::new()
                    .serve_connection(io, service_fn(server_upgrade))
                    .with_upgrades();
                if let Err(e) = conn_fut.await {
                    println!("An error occurred: {:?}", e);
                }
            });
        }
    })
}
