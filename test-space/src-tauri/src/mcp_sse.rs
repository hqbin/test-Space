use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use futures_util::StreamExt;
use serde::Serialize;
use sse_reqwest_client::{RequestBuilderExt, SseEvent};
use reqwest::Client;
use tokio::sync::broadcast;

#[derive(Serialize)]
pub struct McpSseInitResult {
    pub session_id: String,
    pub message_endpoint: String,
}

struct ActiveConnection {
    session_id: String,
    message_endpoint: String,
    close_flag: Arc<std::sync::atomic::AtomicBool>,
    response_rx: broadcast::Receiver<String>,
    client: Client,
}

pub struct SseState(std::sync::Mutex<HashMap<String, ActiveConnection>>);

impl Default for SseState {
    fn default() -> Self {
        SseState(std::sync::Mutex::new(HashMap::new()))
    }
}

fn resolve_url(base: &str, relative: &str) -> String {
    if relative.starts_with("http://") || relative.starts_with("https://") {
        return relative.to_string();
    }
    let origin = if let Some(rest) = base.strip_prefix("https://") {
        let host = rest.split('/').next().unwrap_or(rest);
        format!("https://{}", host)
    } else if let Some(rest) = base.strip_prefix("http://") {
        let host = rest.split('/').next().unwrap_or(rest);
        format!("http://{}", host)
    } else {
        base.trim_end_matches('/').to_string()
    };
    let relative = relative.trim_start_matches('/');
    format!("{}/{}", origin, relative)
}

fn percent_encode(s: &str) -> String {
    let mut out = String::new();
    for &b in s.as_bytes() {
        match b {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => out.push(b as char),
            b' ' => out.push_str("%20"),
            _ => out.push_str(&format!("%{:02X}", b)),
        }
    }
    out
}

fn extract_session_from_url(url: &str) -> Option<String> {
    let after_q = url.split('?').nth(1)?;
    for pair in after_q.split('&') {
        let parts: Vec<&str> = pair.splitn(2, '=').collect();
        if parts.len() == 2 && parts[0] == "session_id" {
            return Some(parts[1].to_string());
        }
    }
    None
}

#[tauri::command]
pub async fn mcp_sse_init(
    server_id: String,
    endpoint: String,
    auth_headers: HashMap<String, String>,
    state: tauri::State<'_, SseState>,
) -> Result<McpSseInitResult, String> {
    {
        let mut map = state.0.lock().map_err(|e| e.to_string())?;
        if let Some(old) = map.remove(&server_id) {
            old.close_flag.store(true, std::sync::atomic::Ordering::Relaxed);
        }
    }

    // CRITICAL: no `.timeout()` for SSE (kills persistent connections)
    let client = Client::builder()
        .connect_timeout(Duration::from_secs(10))
        .tcp_keepalive(Duration::from_secs(15))
        .build()
        .map_err(|e| format!("HTTP client build failed: {}", e))?;

    let mut req = client.get(&endpoint);
    for (name, value) in &auth_headers {
        if !name.is_empty() && !value.is_empty() {
            req = req.header(name.as_str(), value.as_str());
        }
    }

    // into_event_source() handles the GET + SSE parsing + auto-reconnect
    let mut event_stream = req.into_event_source();
    let mut session_id: Option<String> = None;
    let mut msg_endpoint: Option<String> = None;

    let init_timeout = Duration::from_secs(15);
    let start = std::time::Instant::now();
    let init_ok = loop {
        if start.elapsed() >= init_timeout {
            break false;
        }
        match tokio::time::timeout(Duration::from_secs(5), event_stream.next()).await {
            Ok(Some(Ok(event))) => {
                match event {
                    SseEvent::Open => {
                        log::info!("[MCP SSE] Connection opened for {}", endpoint);
                    }
                    SseEvent::Message(msg) => {
                        let et: &str = &msg.event;
                        let ed = msg.data.trim().to_string();
                        log::info!("[MCP SSE] event='{}' data='{:.120}'", et, ed);
                        match et {
                            "session_id" | "sessionId" => session_id = Some(ed),
                            "endpoint" => msg_endpoint = Some(resolve_url(&endpoint, &ed)),
                            _ => {}
                        }
                    }
                    SseEvent::Error(err) => {
                        log::warn!("[MCP SSE] Non-fatal event error: {:?}", err);
                    }
                }
            }
            Ok(Some(Err(e))) => {
                log::error!("[MCP SSE] Fatal stream error: {}", e);
                return Err(format!("SSE fatal error: {}", e));
            }
            Ok(None) => {
                log::warn!("[MCP SSE] Stream ended");
                break false;
            }
            Err(_) => {} // per-read timeout, keep trying
        }
        if msg_endpoint.is_some() || session_id.is_some() {
            break true;
        }
    };

    if !init_ok && msg_endpoint.is_none() && session_id.is_none() {
        return Err("SSE: no endpoint or session_id event received within 15s".to_string());
    }

    let mep = msg_endpoint.clone().unwrap_or_else(|| {
        let base = endpoint
            .trim_end_matches('/')
            .strip_suffix("/sse")
            .unwrap_or(endpoint.trim_end_matches('/'))
            .trim_end_matches('/');
        format!("{}/message", base)
    });
    log::info!("[MCP SSE] message_endpoint = {}", mep);

    let sid = session_id.clone().unwrap_or_else(|| {
        extract_session_from_url(&mep).unwrap_or_else(|| "auto".to_string())
    });
    log::info!("[MCP SSE] session_id = {}", sid);

    let close_flag = Arc::new(std::sync::atomic::AtomicBool::new(false));
    let close_flag_clone = close_flag.clone();
    let (tx, rx) = broadcast::channel(256);
    let bg_tx = tx.clone();
    let sid_for_bg = server_id.clone();

    // Background: keep alive + forward message events to broadcast channel
    tokio::spawn(async move {
        log::info!("[MCP SSE] Background reader started for {}", sid_for_bg);
        while !close_flag_clone.load(std::sync::atomic::Ordering::Relaxed) {
            match tokio::time::timeout(Duration::from_secs(60), event_stream.next()).await {
                Ok(Some(Ok(event))) => {
                    if let SseEvent::Message(msg) = event {
                        if !msg.data.is_empty() {
                            log::info!("[MCP SSE] BG event '{}' ({:.80})", msg.event, msg.data);
                            let _ = bg_tx.send(msg.data);
                        }
                    }
                }
                Ok(Some(Err(e))) => {
                    log::error!("[MCP SSE] Background fatal error: {}", e);
                    break;
                }
                Ok(None) => {
                    log::info!("[MCP SSE] Background stream ended");
                    break;
                }
                Err(_) => {} // 60s timeout, keep alive
            }
        }
        log::info!("[MCP SSE] Background reader stopped for {}", sid_for_bg);
    });

    {
        let mut map = state.0.lock().map_err(|e| e.to_string())?;
        map.insert(server_id, ActiveConnection {
            session_id: sid.clone(),
            message_endpoint: mep.clone(),
            close_flag,
            response_rx: rx,
            client: client,
        });
    }

    Ok(McpSseInitResult { session_id: sid, message_endpoint: mep })
}

#[tauri::command]
pub async fn mcp_sse_call(
    server_id: String,
    body: String,
    state: tauri::State<'_, SseState>,
) -> Result<String, String> {
    let (session_id, message_endpoint, response_rx, post_client) = {
        let map = state.0.lock().map_err(|e| e.to_string())?;
        let conn = map.get(&server_id).ok_or_else(|| "SSE connection not found".to_string())?;
        (conn.session_id.clone(), conn.message_endpoint.clone(), conn.response_rx.resubscribe(), conn.client.clone())
    };

    // Append session_id only if not already in the URL
    let post_url = if message_endpoint.contains("session_id=") {
        message_endpoint.clone()
    } else {
        format!("{}?session_id={}", message_endpoint, percent_encode(&session_id))
    };
    log::info!("[MCP SSE] POST to {}", post_url);

    let post_resp = match post_client
        .post(&post_url)
        .header("Content-Type", "application/json")
        .body(body.clone())
        .send()
        .await
    {
        Ok(r) => r,
        Err(e) => return Err(format!("POST to message endpoint failed: {}", e)),
    };

    let status = post_resp.status();
    log::info!("[MCP SSE] POST returned HTTP {}", status);

    // Try direct HTTP response first
    match post_resp.text().await {
        Ok(text) if !text.is_empty() => {
            let trimmed = text.trim();
            log::info!("[MCP SSE] Response body ({:.120})", trimmed);
            if trimmed.starts_with('{') || trimmed.starts_with('[') {
                return Ok(text);
            }
            // Not JSON-RPC — fall through to SSE wait, include body in final error
        }
        Ok(_) => {
            log::warn!("[MCP SSE] POST returned empty body");
        }
        Err(e) => {
            log::error!("[MCP SSE] Failed to read response body: {}", e);
        }
    }

    // Wait for response on SSE stream
    let mut rx = response_rx;
    let req_id = extract_json_rpc_id(&body);
    let timeout = Duration::from_secs(30);
    let start = std::time::Instant::now();

    log::info!("[MCP SSE] Waiting for SSE response (req_id={:?})", req_id);

    while start.elapsed() < timeout {
        match tokio::time::timeout(Duration::from_secs(5), rx.recv()).await {
            Ok(Ok(data)) => {
                if let Some(ref rid) = req_id {
                    if data.contains(&format!("\"id\":{}", rid)) || data.contains(&format!("\"id\":\"{}\"", rid)) {
                        log::info!("[MCP SSE] Matched response id={}", rid);
                        return Ok(data);
                    }
                } else {
                    return Ok(data);
                }
            }
            Ok(Err(broadcast::error::RecvError::Lagged(n))) => {
                log::warn!("[MCP SSE] Lagged by {} messages", n);
                continue;
            }
            Ok(Err(broadcast::error::RecvError::Closed)) => {
                log::warn!("[MCP SSE] Channel closed");
                break;
            }
            Err(_) => {} // timeout on recv
        }
    }

    Err(format!("SSE: no response within 30s (POST status={})", status))
}

#[tauri::command]
pub async fn mcp_sse_close(
    server_id: String,
    state: tauri::State<'_, SseState>,
) -> Result<(), String> {
    let mut map = state.0.lock().map_err(|e| e.to_string())?;
    if let Some(conn) = map.remove(&server_id) {
        conn.close_flag.store(true, std::sync::atomic::Ordering::Relaxed);
        log::info!("[MCP SSE] Closed {}", server_id);
    }
    Ok(())
}

fn extract_json_rpc_id(body: &str) -> Option<String> {
    if let Ok(val) = serde_json::from_str::<serde_json::Value>(body) {
        val.get("id").map(|id| id.to_string())
    } else {
        None
    }
}
