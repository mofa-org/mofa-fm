use dora_node_api::{dora_core::config::DataId, DoraNode, Event};
use eyre::Result;
use std::env;
use std::fs;
use std::io::Write;
use std::path::PathBuf;

fn main() -> Result<()> {
    let port = env::var("PORT").unwrap_or_else(|_| "8001".to_string());

    eprintln!("[WS-{}] Starting Dora node", port);
    std::io::stderr().flush().ok();

    // 消息文件路径
    let msg_dir = PathBuf::from(format!("/tmp/dora-ws-{}", port));
    fs::create_dir_all(&msg_dir).ok();

    // 清空旧消息
    if let Ok(entries) = fs::read_dir(&msg_dir) {
        for entry in entries.flatten() {
            fs::remove_file(entry.path()).ok();
        }
    }

    // 初始化Dora节点 - 纯输出节点不需要events
    let (mut node, _events) = DoraNode::init_from_env()?;

    // 确认init成功
    std::fs::write(format!("/tmp/ws-{}-init-ok.txt", port), "init successful").ok();

    eprintln!("[WS-{}] ✓ Dora node ready", port);
    eprintln!("[WS-{}] Message dir: {}", port, msg_dir.display());
    std::io::stderr().flush().ok();

    let mut msg_counter: u64 = 0;

    // 轮询文件并发送（纯输出节点模式）
    loop {
        // 检查新消息文件
        if let Ok(entries) = fs::read_dir(&msg_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if let Ok(content) = fs::read_to_string(&path) {
                    eprintln!("[WS-{}] → Dora: {}", port, &content[..content.len().min(50)]);

                    // 发送到Dora
                    let output_id: DataId = "text".to_string().into();
                    let string_array = arrow::array::StringArray::from(vec![content.as_str()]);

                    if let Err(e) = node.send_output(output_id, Default::default(), string_array) {
                        eprintln!("[WS-{}] Send error: {}", port, e);
                    } else {
                        // 成功后删除文件
                        fs::remove_file(&path).ok();
                        msg_counter += 1;
                    }
                }
            }
        }

        // 短暂休眠避免CPU占用
        std::thread::sleep(std::time::Duration::from_millis(100));
    }

    // 清理
    fs::remove_dir_all(&msg_dir).ok();
    Ok(())
}
