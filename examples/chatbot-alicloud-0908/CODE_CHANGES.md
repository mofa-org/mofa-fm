# Code Changes for Moly Client Integration with Dora WebSocket Server

## Overview
This document details the extensive refactoring and bug fixes required to integrate the Moly client (OpenAI Realtime API compatible client) with Dora's WebSocket server. The work involved multiple iterations to achieve proper voice activity detection (VAD), audio routing, and conversation flow management.

## Problem Statement
The Moly client was getting stuck in listening mode after playing the initial greeting and wouldn't respond to voice input. This required a complete overhaul of the dataflow architecture and VAD implementation.

## Major Architectural Changes

### 1. Refactored to Static + Dynamic Dataflow Architecture

**Rationale**: Persistent nodes (speech-monitor, ASR, TTS) should run continuously, while connection-specific nodes (wserver, maas-client) should be created per client connection.

**Implementation**:
- Created `static-dataflow.yml` for persistent audio processing pipeline
- Modified WebSocket server to spawn dynamic nodes on client connection
- Separated concerns between infrastructure and connection handling

**Files Created/Modified**:
- `/Users/yuechen/home/fresh/dora/examples/chatbot-openai-0905/static-dataflow.yml` (new)
- `/Users/yuechen/home/fresh/dora/examples/chatbot-openai-0905/whisper-template-metal.yml` (modified)
- `/Users/yuechen/home/fresh/dora/node-hub/dora-openai-websocket/src/main.rs` (extensively modified)

### 2. Implemented Segment Counting and Conversation Tracking

**Purpose**: Track conversation flow and ensure proper completion signaling to Moly client.

**Changes in** `/Users/yuechen/home/fresh/dora/node-hub/dora-text-segmenter/dora_text_segmenter/queue_based_segmenter.py`:
```python
# Added segment counter and conversation tracking
segment_counter = 0  # Number of segments in queue
conversation_id = None  # Reset when counter reaches zero

# Generate new conversation ID when counter is 0
if segment_counter == 0:
    conversation_id = str(uuid.uuid4())[:8]
    print(f"[Segmenter] 🆕 New conversation: {conversation_id}")

# Track segments remaining
metadata={
    "segments_remaining": segment_counter,
    "conversation_id": conversation_id,
}
```

**Changes in** `/Users/yuechen/home/fresh/dora/node-hub/dora-primespeech/dora_primespeech/main.py`:
```python
# Propagate segment metadata through audio pipeline
node.send_output(
    "segment_complete",
    pa.array(["completed"]),
    metadata={
        "segments_remaining": metadata.get("segments_remaining", 0),
        "conversation_id": metadata.get("conversation_id")
    }
)
```

### 3. Fixed Event Ordering for Proper Audio Completion

**Problem**: Audio was being sent after completion events, causing Moly to misinterpret conversation state.

**Solution in** `/Users/yuechen/home/fresh/dora/node-hub/dora-openai-websocket/src/main.rs`:
```rust
// Send completion events immediately after last audio frame
if segments_remaining == 0 {
    // Send response.audio.done
    let audio_done = OpenAIRealtimeResponse::ResponseAudioDone { 
        // ... 
    };
    
    // Send response.done
    let response_done = OpenAIRealtimeResponse::ResponseDone {
        // ...
    };
    
    // Send both events in same iteration as last audio
}
```

### 4. Implemented Proper VAD with `question_ended` Event

**Critical Change**: System now waits for complete sentences before triggering LLM responses.

**Modified** `/Users/yuechen/home/fresh/dora/node-hub/dora-openai-websocket/src/main.rs`:
```rust
// Before: Triggered on every speech fragment
} else if id.contains("speech_stopped") || id.contains("speech_ended") {

// After: Triggers only on complete questions (3 seconds of silence)
} else if id.contains("question_ended") {
    println!("❓ Question ended detected - complete sentence, triggering LLM response");
```

**Updated** `whisper-template-metal.yml`:
```yaml
inputs:
  question_ended: speech-monitor/question_ended  # Added this input
```

### 5. Fixed Audio Pipeline Routing

**Problem**: Audio from Moly wasn't reaching speech-monitor due to incorrect connections.

**Fixed in** `whisper-template-metal.yml`:
```yaml
# Speech-monitor now receives from wserver (not non-existent mac-aec)
- id: speech-monitor
  inputs:
    audio:
      source: wserver/audio  # Changed from mac-aec/audio

# ASR now receives from speech-monitor (not mac-aec)
- id: asr
  inputs:
    audio:
      source: speech-monitor/audio_segment  # Changed from mac-aec/audio_segment
```

### 6. Enhanced Audio Buffer Processing

**Implemented proper audio buffering and resampling**:
```rust
// Process audio in fixed-size chunks for consistent processing
const DOWNSAMPLE_CHUNK_SIZE: usize = 24000 * 2; // 2 seconds at 24kHz

while audio_buffer.len() >= DOWNSAMPLE_CHUNK_SIZE {
    let chunk: Vec<f32> = audio_buffer.drain(..DOWNSAMPLE_CHUNK_SIZE).collect();
    // Resample from 24kHz to 16kHz for speech processing
    let output = downsampler.process(&input, None).expect("Resampling failed");
    // Send to speech-monitor
}
```

### 7. Implemented Greeting and Session Management

**Added initial greeting support**:
```rust
// Send greeting when session starts
let greeting = "你好！有什么可以帮助你的吗？";
node.send_output(
    DataId::from("text".to_string()),
    MetadataParameters::default(),
    greeting.into_arrow(),
)?;
```

### 8. Cleaned Up Logging and Debugging

**Removed verbose logging**:
```rust
// Commented out noisy audio buffer logs
// println!("📡 Received audio buffer from client, base64 length: {}", audio.len());
```

## Complete Audio Flow Architecture

```
┌─────────────┐     WebSocket      ┌──────────┐
│ Moly Client │ ◄──────────────────► │ wserver  │
└─────────────┘                     └─────┬────┘
                                          │ audio
                                          ▼
                                   ┌──────────────┐
                                   │speech-monitor│
                                   └─────┬────┬───┘
                            audio_segment│    │question_ended
                                         ▼    ▼
                                    ┌──────┐  trigger
                                    │ ASR  │  LLM
                                    └──┬───┘
                               transcription│
                                            ▼
                                    ┌──────────────┐
                                    │ maas-client  │
                                    └──────┬───────┘
                                           │text
                                           ▼
                                    ┌──────────────┐
                                    │text-segmenter│
                                    └──────┬───────┘
                                           │text_segment
                                           ▼
                                    ┌──────────────┐
                                    │ primespeech  │
                                    └──────┬───────┘
                                           │audio
                                           ▼
                                      Back to Moly
```

## Event Sequence for Complete Conversation

1. **User speaks**: Audio streams from Moly to wserver
2. **VAD detection**: speech-monitor detects speech patterns
3. **Real-time transcription**: ASR processes audio segments as they arrive
4. **Question detection**: After 3 seconds of silence, `question_ended` fires
5. **LLM trigger**: wserver commits audio buffer and triggers response
6. **Response generation**: maas-client generates response
7. **Text segmentation**: text-segmenter breaks response into speakable chunks
8. **TTS synthesis**: primespeech converts text to audio
9. **Audio streaming**: Audio streams back to Moly with proper completion events
10. **Conversation reset**: When segments_remaining reaches 0, conversation resets

## Key Problems Solved

1. **Moly stuck in listening mode**: Fixed by implementing proper server-side VAD
2. **Audio not reaching pipeline**: Fixed pipeline connections
3. **Premature LLM triggers**: Now waits for complete questions
4. **Event ordering issues**: Audio and completion events now properly sequenced
5. **Session management**: Proper greeting and conversation tracking
6. **Memory management**: Fixed memory leaks in audio buffering

## Testing Checklist

- [x] Moly client connects successfully
- [x] Initial greeting plays
- [x] Client transitions from listening after greeting
- [x] Speech detection works (speech_started/speech_ended events)
- [x] Complete question detection (question_ended after 3s silence)
- [x] ASR transcribes Chinese correctly
- [x] LLM generates appropriate responses
- [x] TTS synthesizes audio properly
- [x] Audio streams back to client
- [x] Completion events sent in correct order
- [x] Conversation can continue multiple turns

## Environment Configuration

Required environment variables in dataflow:
```yaml
QUESTION_END_SILENCE_MS: 3000  # 3 seconds for question completion
USER_SILENCE_THRESHOLD_MS: 1500  # 1.5s for speech end
VAD_THRESHOLD: 0.6  # Voice activity detection threshold
SAMPLE_RATE: 16000  # Audio sample rate for processing
```

## Acknowledgments

This integration required extensive debugging and iteration to properly support the Moly client's expectations of the OpenAI Realtime API protocol. The key insight was that Moly expects server-side VAD with proper `question_ended` detection, not just simple speech fragment processing. The static/dynamic dataflow separation ensures efficient resource usage while maintaining connection isolation.