// This is a restructured version that connects to dataflow immediately at startup
// The key changes:
// 1. Parse --name argument in main()
// 2. Connect to dataflow as wserver immediately
// 3. Spawn maas-client immediately
// 4. Share the Dora node connection across all client sessions

use std::sync::Arc;
use tokio::sync::Mutex;
use std::env;

// Structure to hold the shared Dora node connection
struct SharedDoraNode {
    node: Arc<Mutex<Option<DoraNode>>>,
    events: Arc<Mutex<Option<EventStream>>>,
}

fn main() -> Result<(), WebSocketError> {
    let rt = tokio::runtime::Builder::new_multi_thread()
        .enable_io()
        .enable_time()
        .build()
        .unwrap();

    rt.block_on(async move {
        // Parse command line arguments to check for --name
        let args: Vec<String> = env::args().collect();
        let mut node_name: Option<String> = None;
        
        // Look for --name argument
        for i in 0..args.len() {
            if args[i] == "--name" && i + 1 < args.len() {
                node_name = Some(args[i + 1].clone());
                break;
            }
        }
        
        // Initialize shared Dora connection
        let shared_dora = if let Some(name) = node_name {
            println!("Connecting to dataflow as dynamic node: {}", name);
            
            // Connect to dataflow immediately
            match DoraNode::init_from_node_id(NodeId::from(name.clone())) {
                Ok((node, events)) => {
                    println!("✅ Successfully connected to dataflow as '{}'", name);
                    
                    // Spawn maas-client immediately
                    println!("Spawning maas-client as dynamic node...");
                    let config_path = "/Users/yuechen/home/fresh/dora/examples/chatbot-openai-0905/maas_mcp_browser_config.toml";
                    
                    let maas_process = Command::new("cargo")
                        .arg("run")
                        .arg("-p")
                        .arg("dora-maas-client")
                        .arg("--")
                        .arg("--name")
                        .arg("maas-client")
                        .env("CONFIG", config_path)
                        .spawn();
                    
                    match maas_process {
                        Ok(mut child) => {
                            println!("✅ maas-client spawned with PID: {:?}", child.id());
                            
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
                        Err(e) => {
                            eprintln!("⚠️ Failed to spawn maas-client: {}", e);
                        }
                    }
                    
                    // Start event processing loop in background
                    let events_mutex = Arc::new(Mutex::new(Some(events)));
                    let events_clone = events_mutex.clone();
                    tokio::spawn(async move {
                        let mut events = events_clone.lock().await.take().unwrap();
                        while let Some(event) = events.recv().await {
                            // Process Dora events here
                            println!("Received Dora event: {:?}", event);
                        }
                    });
                    
                    SharedDoraNode {
                        node: Arc::new(Mutex::new(Some(node))),
                        events: events_mutex,
                    }
                }
                Err(e) => {
                    eprintln!("❌ Failed to connect to dataflow as '{}': {:?}", name, e);
                    eprintln!("Make sure the static dataflow is running first");
                    return Err(WebSocketError::InvalidConnectionHeader);
                }
            }
        } else {
            println!("Running in standalone mode (no --name argument provided)");
            SharedDoraNode {
                node: Arc::new(Mutex::new(None)),
                events: Arc::new(Mutex::new(None)),
            }
        };
        
        // Now start the WebSocket server
        let port = std::env::var("PORT").unwrap_or_else(|_| "8123".to_string());
        let host = std::env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let addr = format!("{}:{}", host, port);
        let listener = TcpListener::bind(&addr).await?;
        println!("WebSocket server ready, listening on {}", addr);
        
        loop {
            let (stream, _) = listener.accept().await?;
            println!("Client connected");
            
            let shared_dora_clone = shared_dora.clone();
            
            tokio::spawn(async move {
                let io = hyper_util::rt::TokioIo::new(stream);
                let conn_fut = http1::Builder::new()
                    .serve_connection(io, service_fn(move |req| {
                        let shared_dora = shared_dora_clone.clone();
                        async move {
                            server_upgrade_with_dora(req, shared_dora).await
                        }
                    }))
                    .with_upgrades();
                if let Err(e) = conn_fut.await {
                    println!("An error occurred: {:?}", e);
                }
            });
        }
    })
}

async fn server_upgrade_with_dora(
    mut req: Request<Incoming>,
    shared_dora: SharedDoraNode,
) -> Result<Response<Empty<Bytes>>, WebSocketError> {
    println!("WebSocket upgrade request received");
    
    let (response, fut) = upgrade::upgrade(&mut req)?;
    println!("WebSocket upgrade successful");

    tokio::task::spawn(async move {
        if let Err(e) = handle_client_with_shared_dora(fut, shared_dora).await {
            eprintln!("Error in websocket connection: {}", e);
        }
    });

    Ok(response)
}

async fn handle_client_with_shared_dora(
    fut: impl Future<Output = Result<WebSocket, WebSocketError>>,
    shared_dora: SharedDoraNode,
) -> Result<(), WebSocketError> {
    let mut ws = fut.await?;
    
    // Use the shared Dora node connection
    let node_guard = shared_dora.node.lock().await;
    if node_guard.is_some() {
        println!("Using existing Dora node connection");
        // Handle WebSocket messages and forward to/from Dora
        // ... rest of the WebSocket handling logic ...
    } else {
        println!("Running without Dora connection");
        // Handle WebSocket in standalone mode
    }
    
    Ok(())
}