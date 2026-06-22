use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::oneshot;
use tokio::time::{timeout, Duration};
use uuid::Uuid;
use http_mitm_proxy::{DefaultClient, MitmProxy, RemoteAddr};
use http_mitm_proxy::hyper::service::service_fn;
use http_mitm_proxy::hyper::{Request, Response};
use http_mitm_proxy::hyper::body::Incoming;
use http_body_util::{BodyExt, Full};
use http_body_util::combinators::BoxBody;
use bytes::Bytes;
use http_mitm_proxy::moka::sync::Cache;
use serde::{Serialize, Deserialize};
use tauri::Emitter;
use tauri::Manager;

pub struct ProxyState {
    pub inner: Arc<ProxyInner>,
}

impl ProxyState {
    pub fn new() -> Self {
        Self { inner: Arc::new(ProxyInner::new()) }
    }
}

pub struct ProxyInner {
    pub running: AtomicBool,
    pub breakpoint_enabled: AtomicBool,
    pub breakpoint_url_pattern: Mutex<Option<String>>,
    pub pending_breakpoints: Mutex<HashMap<String, oneshot::Sender<serde_json::Value>>>,
    pub rewrite_rules: Mutex<Vec<RewriteRule>>,
    pub captured_requests: Mutex<Vec<CapturedRequest>>,
    pub shutdown_tx: Mutex<Option<oneshot::Sender<()>>>,
    pub port: Mutex<Option<u16>>,
    pub ca_cert_pem: Mutex<Option<String>>,
    pub ca_key_pem: Mutex<Option<String>>,
}

impl ProxyInner {
    pub fn new() -> Self {
        Self {
            running: AtomicBool::new(false),
            breakpoint_enabled: AtomicBool::new(false),
            breakpoint_url_pattern: Mutex::new(None),
            pending_breakpoints: Mutex::new(HashMap::new()),
            rewrite_rules: Mutex::new(Vec::new()),
            captured_requests: Mutex::new(Vec::new()),
            shutdown_tx: Mutex::new(None),
            port: Mutex::new(None),
            ca_cert_pem: Mutex::new(None),
            ca_key_pem: Mutex::new(None),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapturedRequest {
    pub id: String,
    pub method: String,
    pub url: String,
    pub host: String,
    pub path: String,
    pub query: Option<String>,
    pub request_headers: Vec<Vec<String>>,
    pub request_body: Option<String>,
    pub response_status_code: Option<u16>,
    pub response_status_text: Option<String>,
    pub response_headers: Option<Vec<Vec<String>>>,
    pub response_body: Option<String>,
    pub start_time: f64,
    pub end_time: Option<f64>,
    pub duration: Option<f64>,
    pub is_https: bool,
    pub request_size: u64,
    pub response_size: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RewriteRule {
    pub id: String,
    pub name: String,
    pub enabled: bool,
    pub url_pattern: String,
    pub match_type: String,
    pub action_type: String,
    pub header_name: Option<String>,
    pub header_value: Option<String>,
    pub body_search: Option<String>,
    pub body_replace: Option<String>,
    pub redirect_url: Option<String>,
    pub status_code: Option<u16>,
}

fn get_timestamp() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs_f64()
}

fn headers_to_vec(headers: &http_mitm_proxy::hyper::http::HeaderMap) -> Vec<Vec<String>> {
    let mut result = Vec::new();
    for (name, value) in headers.iter() {
        result.push(vec![
            name.to_string(),
            value.to_str().unwrap_or("<binary>").to_string(),
        ]);
    }
    result
}

fn find_available_port() -> Result<u16, String> {
    let listener = std::net::TcpListener::bind("127.0.0.1:0")
        .map_err(|e| format!("Cannot bind: {}", e))?;
    let port = listener.local_addr()
        .map_err(|e| format!("Cannot get addr: {}", e))?
        .port();
    Ok(port)
}

fn get_local_ip() -> Result<String, String> {
    let socket = std::net::UdpSocket::bind("0.0.0.0:0")
        .map_err(|e| format!("Cannot create socket: {}", e))?;
    socket.connect("8.8.8.8:80")
        .map_err(|e| format!("Cannot determine local IP (check network connection): {}", e))?;
    let local_addr = socket.local_addr()
        .map_err(|e| format!("Cannot get local addr: {}", e))?;
    Ok(local_addr.ip().to_string())
}

fn box_body(bytes: Bytes) -> BoxBody<Bytes, http_mitm_proxy::hyper::Error> {
    Full::from(bytes)
        .map_err(|never| match never {})
        .boxed()
}

async fn read_body_bytes(body: Incoming) -> Bytes {
    match BodyExt::collect(body).await {
        Ok(collected) => collected.to_bytes(),
        Err(_) => Bytes::new(),
    }
}

fn url_matches(url: &str, pattern: &str, match_type: &str) -> bool {
    match match_type {
        "exact" => url == pattern,
        _ => url.contains(pattern),
    }
}

fn make_ca_params() -> rcgen::CertificateParams {
    let mut params = rcgen::CertificateParams::new(vec!["TestSpace MITM Proxy CA".to_string()])
        .expect("valid CA params");
    params.distinguished_name = rcgen::DistinguishedName::new();
    params.distinguished_name.push(
        rcgen::DnType::CommonName,
        "TestSpace MITM Proxy CA",
    );
    params.key_usages = vec![
        rcgen::KeyUsagePurpose::KeyCertSign,
        rcgen::KeyUsagePurpose::CrlSign,
    ];
    params.is_ca = rcgen::IsCa::Ca(rcgen::BasicConstraints::Unconstrained);
    params
}

#[tauri::command]
pub async fn proxy_start(
    app: tauri::AppHandle,
    state: tauri::State<'_, ProxyState>,
    device_serial: Option<String>,
) -> Result<String, String> {
    let inner = &state.inner;
    if inner.running.load(Ordering::Acquire) {
        return Err("Proxy is already running".to_string());
    }

    let port = find_available_port()?;
    app.emit("proxy:debug", format!("[proxy] 分配端口: {}", port)).ok();

    let app_data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Cannot get app data dir: {}", e))?;
    std::fs::create_dir_all(&app_data_dir)
        .map_err(|e| format!("Cannot create app data dir: {}", e))?;

    let ca_cert_path = app_data_dir.join("mitm-ca-cert.pem");
    let ca_key_path = app_data_dir.join("mitm-ca-key.pem");

    let (cert_pem, key_pem) = if ca_cert_path.exists() && ca_key_path.exists() {
        let cp = std::fs::read_to_string(&ca_cert_path)
            .map_err(|e| format!("Cannot read CA cert: {}", e))?;
        let kp = std::fs::read_to_string(&ca_key_path)
            .map_err(|e| format!("Cannot read CA key: {}", e))?;
        (cp, kp)
    } else {
        let params = make_ca_params();
        let signing_key = rcgen::KeyPair::generate()
            .map_err(|e| format!("Cannot generate key: {}", e))?;
        let cert = params.self_signed(&signing_key)
            .map_err(|e| format!("Cannot sign cert: {}", e))?;
        let cp = cert.pem();
        let kp = signing_key.serialize_pem();
        std::fs::write(&ca_cert_path, &cp)
            .map_err(|e| format!("Cannot save CA cert: {}", e))?;
        std::fs::write(&ca_key_path, &kp)
            .map_err(|e| format!("Cannot save CA key: {}", e))?;
        (cp, kp)
    };

    *inner.ca_cert_pem.lock().unwrap() = Some(cert_pem.clone());
    *inner.ca_key_pem.lock().unwrap() = Some(key_pem.clone());

    let ca_key = rcgen::KeyPair::from_pem(&key_pem)
        .map_err(|e| format!("Cannot parse CA key: {}", e))?;
    let ca_params = make_ca_params();
    let root_issuer = rcgen::Issuer::new(ca_params, ca_key);

    inner.running.store(true, Ordering::Release);

    let state_for_handler = inner.clone();
    let app_handle = app.clone();

    let (shutdown_tx, shutdown_rx) = oneshot::channel::<()>();
    *inner.shutdown_tx.lock().unwrap() = Some(shutdown_tx);

    let proxy_port = port;

    let sf_state = state_for_handler.clone();
    let sf_app = app_handle.clone();

    tokio::spawn(async move {
        // 初始化 rustls crypto provider（必须在创建 MitmProxy 之前）
        let _ = rustls::crypto::CryptoProvider::install_default(
            rustls::crypto::ring::default_provider()
        );

        let proxy = MitmProxy::new(Some(root_issuer), Some(Cache::new(128)));
        let client = DefaultClient::new();

        let server_result = proxy.bind(
            ("0.0.0.0", proxy_port),
            service_fn(move |req: Request<Incoming>| {
                let state = sf_state.clone();
                let app_handle = sf_app.clone();
                let client = client.clone();

                async move {
                    let start_time = get_timestamp();
                    let request_id = Uuid::new_v4().to_string();
                    let remote_addr = req.extensions().get::<RemoteAddr>()
                        .map(|r| r.0)
                        .unwrap_or("0.0.0.0:0".parse().unwrap());
                    let uri = req.uri().clone();
                    let is_https = uri.scheme_str() == Some("https");
                    let url = uri.to_string();
                    let host = uri.host().unwrap_or("").to_string();
                    let path = uri.path().to_string();
                    let query = uri.query().map(|q| q.to_string());
                    let method = req.method().to_string();

                    let log_msg = format!("[proxy] >>> {} {} (host={}, from={})", method, url, host, remote_addr);
                    eprintln!("{}", log_msg);
                    app_handle.emit("proxy:debug", &log_msg).ok();

                    let (mut req_parts, req_body) = req.into_parts();
                    let req_body_bytes = read_body_bytes(req_body).await;
                    let req_body_str = if req_body_bytes.is_empty() {
                        None
                    } else {
                        String::from_utf8(req_body_bytes.to_vec()).ok()
                    };

                    let req_headers = headers_to_vec(&req_parts.headers);
                    let req_size = req_body_bytes.len() as u64;

                    let captured = CapturedRequest {
                        id: request_id.clone(),
                        method: method.clone(),
                        url: url.clone(),
                        host: host.clone(),
                        path: path.clone(),
                        query: query.clone(),
                        request_headers: req_headers.clone(),
                        request_body: req_body_str.clone(),
                        response_status_code: None,
                        response_status_text: None,
                        response_headers: None,
                        response_body: None,
                        start_time,
                        end_time: None,
                        duration: None,
                        is_https,
                        request_size: req_size,
                        response_size: 0,
                    };

                    app_handle.emit("proxy:request", &captured).ok();

                    let mut rebuild_body = box_body(req_body_bytes.clone());

                    // Apply request rewrite rules
                    let rules = state.rewrite_rules.lock().unwrap().clone();
                    for rule in &rules {
                        if !rule.enabled { continue; }
                        if !url_matches(&url, &rule.url_pattern, &rule.match_type) { continue; }
                        match rule.action_type.as_str() {
                            "drop" => {
                                return Ok(Response::builder()
                                    .status(502)
                                    .header("X-Proxy", "TestSpace-Rule")
                                    .body(box_body(Bytes::from("请求被重写规则丢弃")))
                                    .unwrap());
                            }
                            "modify_request_header" => {
                                if let (Some(name), Some(value)) = (&rule.header_name, &rule.header_value) {
                                    if let (Ok(n), Ok(v)) = (
                                        http_mitm_proxy::hyper::http::HeaderName::from_bytes(name.as_bytes()),
                                        http_mitm_proxy::hyper::http::HeaderValue::from_str(value),
                                    ) {
                                        req_parts.headers.insert(n, v);
                                    }
                                }
                            }
                            "modify_request_body" => {
                                if let (Some(search), Some(replace)) = (&rule.body_search, &rule.body_replace) {
                                    if let Some(body_str) = &req_body_str {
                                        let new_body = body_str.replace(search, replace);
                                        rebuild_body = box_body(Bytes::from(new_body));
                                    }
                                }
                            }
                            _ => {}
                        }
                    }

                    // Breakpoint check (request)
                    if state.breakpoint_enabled.load(Ordering::Acquire) {
                        let bp_pattern = state.breakpoint_url_pattern.lock().unwrap().clone();
                        let should_break = bp_pattern.as_ref().map_or(true, |p| url_matches(&url, p, "contains"));
                        if should_break {
                            let (tx, rx) = oneshot::channel::<serde_json::Value>();
                            state.pending_breakpoints.lock().unwrap()
                                .insert(request_id.clone(), tx);
                            app_handle.emit("proxy:breakpoint:request", &captured).ok();

                            match timeout(Duration::from_secs(300), rx).await {
                                Ok(Ok(action)) => {
                                    match action.get("type").and_then(|v| v.as_str()).unwrap_or("forward") {
                                        "drop" => return Ok(Response::builder()
                                            .status(502)
                                            .header("X-Proxy", "TestSpace")
                                            .body(box_body(Bytes::from("Request dropped by breakpoint")))
                                            .unwrap()),
                                        "modify" => {
                                            if let Some(_headers) = action.get("headers").and_then(|v| v.as_object()) {
                                            }
                                            if let Some(body_str) = action.get("body").and_then(|v| v.as_str()) {
                                                rebuild_body = box_body(Bytes::from(body_str.to_string()));
                                            }
                                        }
                                        _ => {}
                                    }
                                }
                                _ => {}
                            }
                        }
                    }

                    let rebuilt_req = Request::from_parts(req_parts, rebuild_body);

                    // DefaultClient::send_request() requires the full URL (with scheme + host)
                    // to know where to connect. HTTP proxy requests arrive with absolute-form
                    // URI (http://host/path); hyper internally converts to origin-form on the wire.
                    let fwd_log = format!("[proxy] --> forwarding {} to upstream", url);
                    eprintln!("{}", fwd_log);
                    app_handle.emit("proxy:debug", &fwd_log).ok();
                    let send_fut = client.send_request(rebuilt_req);
                    let response_result = tokio::time::timeout(Duration::from_secs(30), send_fut).await;
                    let (response, end_time, duration) = match response_result {
                        Ok(Ok((res, _upgrade))) => {
                            let end = get_timestamp();
                            let dur = ((end - start_time) * 1000.0 * 100.0).round() / 100.0;
                            let ok_log = format!("[proxy] <<< {} {} ({}ms)", url, res.status(), dur);
                            eprintln!("{}", ok_log);
                            app_handle.emit("proxy:debug", &ok_log).ok();
                            (res, Some(end), Some(dur))
                        }
                        Ok(Err(e)) => {
                            let err_log = format!("[proxy] ERROR {}: {}", url, e);
                            eprintln!("{}", err_log);
                            app_handle.emit("proxy:debug", &err_log).ok();
                            return Ok(Response::builder()
                                .status(502)
                                .header("X-Proxy", "TestSpace-Error")
                                .body(box_body(Bytes::from(format!("Proxy error: {}", e))))
                                .unwrap());
                        }
                        Err(_) => {
                            let timeout_log = format!("[proxy] TIMEOUT {} (30s)", url);
                            eprintln!("{}", timeout_log);
                            app_handle.emit("proxy:debug", &timeout_log).ok();
                            return Ok(Response::builder()
                                .status(504)
                                .header("X-Proxy", "TestSpace-Timeout")
                                .body(box_body(Bytes::from("Proxy upstream request timed out after 30s")))
                                .unwrap());
                        }
                    };

                    let (mut res_parts, res_body) = response.into_parts();
                    let res_body_bytes = read_body_bytes(res_body).await;
                    let res_body_str = if res_body_bytes.is_empty() {
                        None
                    } else {
                        String::from_utf8(res_body_bytes.to_vec()).ok()
                    };

                    let res_headers = headers_to_vec(&res_parts.headers);
                    let status_code = res_parts.status.as_u16();
                    let status_text = res_parts.status.canonical_reason()
                        .unwrap_or("Unknown")
                        .to_string();
                    let res_size = res_body_bytes.len() as u64;

                    let full_captured = CapturedRequest {
                        response_status_code: Some(status_code),
                        response_status_text: Some(status_text),
                        response_headers: Some(res_headers.clone()),
                        response_body: res_body_str.clone(),
                        end_time,
                        duration,
                        response_size: res_size,
                        ..captured
                    };

                    {
                        let mut stored = state.captured_requests.lock().unwrap();
                        stored.push(full_captured.clone());
                        let overflow = stored.len().saturating_sub(1000);
                        if overflow > 0 {
                            stored.drain(0..overflow);
                        }
                    }

                    app_handle.emit("proxy:response", &full_captured).ok();

                    let mut final_body = box_body(res_body_bytes.clone());
                    let mut final_status = status_code;

                    // Apply response rewrite rules
                    let rules = state.rewrite_rules.lock().unwrap().clone();
                    for rule in &rules {
                        if !rule.enabled { continue; }
                        if !url_matches(&url, &rule.url_pattern, &rule.match_type) { continue; }
                        match rule.action_type.as_str() {
                            "modify_response_header" => {
                                if let (Some(name), Some(value)) = (&rule.header_name, &rule.header_value) {
                                    if let (Ok(n), Ok(v)) = (
                                        http_mitm_proxy::hyper::http::HeaderName::from_bytes(name.as_bytes()),
                                        http_mitm_proxy::hyper::http::HeaderValue::from_str(value),
                                    ) {
                                        res_parts.headers.insert(n, v);
                                    }
                                }
                            }
                            "modify_response_body" => {
                                if let (Some(search), Some(replace)) = (&rule.body_search, &rule.body_replace) {
                                    if let Some(body_str) = &res_body_str {
                                        let new_body = body_str.replace(search, replace);
                                        final_body = box_body(Bytes::from(new_body));
                                    }
                                }
                            }
                            _ => {}
                        }
                    }

                    // Breakpoint check (response)
                    if state.breakpoint_enabled.load(Ordering::Acquire) {
                        let bp_pattern = state.breakpoint_url_pattern.lock().unwrap().clone();
                        let should_break = bp_pattern.as_ref().map_or(true, |p| url_matches(&url, p, "contains"));
                        if should_break {
                            let resp_id = format!("{}_resp", request_id);
                            let (tx, rx) = oneshot::channel::<serde_json::Value>();
                            state.pending_breakpoints.lock().unwrap()
                                .insert(resp_id, tx);
                            app_handle.emit("proxy:breakpoint:response", &full_captured).ok();

                            match timeout(Duration::from_secs(300), rx).await {
                                Ok(Ok(action)) => {
                                    match action.get("type").and_then(|v| v.as_str()).unwrap_or("forward") {
                                        "drop" => return Ok(Response::builder()
                                            .status(502)
                                            .header("X-Proxy", "TestSpace")
                                            .body(box_body(Bytes::from("Response dropped by breakpoint")))
                                            .unwrap()),
                                        "modify" => {
                                            if let Some(s) = action.get("status_code").and_then(|v| v.as_u64()) {
                                                final_status = s as u16;
                                            }
                                            if let Some(body_str) = action.get("body").and_then(|v| v.as_str()) {
                                                final_body = box_body(Bytes::from(body_str.to_string()));
                                            }
                                        }
                                        _ => {}
                                    }
                                }
                                _ => {}
                            }
                        }
                    }

                    let mut final_res = Response::from_parts(res_parts, final_body);
                    *final_res.status_mut() = http_mitm_proxy::hyper::StatusCode::from_u16(final_status)
                        .unwrap_or(http_mitm_proxy::hyper::StatusCode::BAD_GATEWAY);

                    Ok::<_, std::convert::Infallible>(final_res)
                }
            }),
        ).await;

        match server_result {
            Ok(server_handle) => {
                app_handle.emit("proxy:debug", format!("[proxy] 代理服务器已在 0.0.0.0:{} 监听", proxy_port)).ok();
                // server_handle 是 accept 循环的 future，必须 poll 它才能接受连接
                tokio::select! {
                    _ = server_handle => {
                        eprintln!("[proxy] 服务器 accept 循环意外结束");
                    }
                    _ = shutdown_rx => {
                        eprintln!("[proxy] 收到关闭信号");
                    }
                }
            }
            Err(e) => {
                app_handle.emit("proxy:error", format!("启动代理失败: {}", e)).ok();
            }
        }

        state_for_handler.running.store(false, Ordering::Release);
    });

    *inner.port.lock().unwrap() = Some(port);
    let mut messages = vec![format!("代理已启动，端口：{}", port)];

    if let Some(ref serial) = device_serial {
        // 1. 推送 CA 证书
        {
            let tmp_dir = std::env::temp_dir();
            let cert_path = tmp_dir.join("testspace-ca-cert.pem");
            std::fs::write(&cert_path, &cert_pem)
                .map_err(|e| format!("写入证书失败：{}", e))?;

            let push_serial = serial.clone();
            let cp = cert_path.to_string_lossy().to_string();
            match tokio::task::spawn_blocking(move || {
                crate::adb::push_file(&push_serial, &cp, "/sdcard/testspace-ca-cert.pem")
            }).await.map_err(|e| e.to_string())? {
                Ok(_) => app.emit("proxy:debug", "[proxy] 证书已推送到设备").ok(),
                Err(e) => app.emit("proxy:error", format!("推送证书失败：{}", e)).ok(),
            };
        }

        // 2. Root + 安装系统证书（不用重启，直接生效）
        let cert_ok = try_install_system_cert(serial, &cert_pem, &app).await;
        if cert_ok {
            messages.push("✅ 系统 CA 证书已安装".to_string());
        } else {
            // root/remount 失败，尝试直接拉起用户证书安装
            app.emit("proxy:debug", "[proxy] 尝试用户证书模式...").ok();
            let cert_intents = [
                "cp /sdcard/testspace-ca-cert.pem /sdcard/Download/ 2>/dev/null; \
                 am start -n com.android.certinstaller/.CertInstallerMain \
                 -a android.intent.action.VIEW \
                 -t application/x-x509-ca-cert \
                 -d file:///sdcard/Download/testspace-ca-cert.pem",
                "am start -n com.android.certinstaller/.CertInstallerMain -a android.intent.action.VIEW -t application/x-x509-ca-cert -d file:///sdcard/testspace-ca-cert.pem",
                "am start -a android.settings.SECURITY_SETTINGS",
            ];
            for intent in &cert_intents {
                let sp_serial = serial.clone();
                let cmd = intent.to_string();
                if let Ok(Ok(out)) = tokio::task::spawn_blocking(move || {
                    crate::adb::shell_command(&sp_serial, &cmd)
                }).await {
                    if !out.contains("Error") && !out.contains("not found") {
                        break;
                    }
                }
            }
            messages.push("⚠️ 用户证书模式（仅部分应用可抓 HTTPS）".to_string());
        }

        // 3. 设置设备代理
        let proxy_host = get_local_ip().unwrap_or_else(|_| "127.0.0.1".to_string());
        app.emit("proxy:debug", format!("[proxy] 使用 LAN IP: {} 设置设备代理", proxy_host)).ok();
        let proxy_serial = serial.clone();
        let proxy_host_clone = proxy_host.clone();
        match tokio::task::spawn_blocking(move || {
            crate::adb::shell_command(&proxy_serial,
                &format!("settings put global http_proxy {}:{}", proxy_host_clone, port)
            )
        }).await.map_err(|e| e.to_string())? {
            Ok(_) => messages.push(format!("📡 设备代理已指向 {}:{}", proxy_host, port)),
            Err(e) => messages.push(format!("⚠️ 设置代理失败：{}", e)),
        }
    }

    Ok(messages.join("\n---\n"))
}

#[tauri::command]
pub async fn proxy_stop(
    state: tauri::State<'_, ProxyState>,
    device_serial: Option<String>,
) -> Result<String, String> {
    let inner = &state.inner;
    if !inner.running.load(Ordering::Acquire) {
        return Err("代理未运行".to_string());
    }
    let mut messages = vec![];
    if let Some(ref serial) = device_serial {
        let clear_serial = serial.clone();
        match tokio::task::spawn_blocking(move || {
            crate::adb::shell_command(&clear_serial, "settings put global http_proxy :0")
        }).await.map_err(|e| e.to_string())? {
            Ok(_) => messages.push(format!("📡 设备 {} 的代理已清除", serial)),
            Err(e) => messages.push(format!("⚠️ 清除设备代理失败：{}", e)),
        }
    }
    if let Some(tx) = inner.shutdown_tx.lock().unwrap().take() {
        let _ = tx.send(());
    }
    // Give the proxy task a moment to process the shutdown signal
    tokio::time::sleep(std::time::Duration::from_millis(100)).await;
    inner.running.store(false, Ordering::Release);
    *inner.port.lock().unwrap() = None;
    messages.push("🛑 代理已停止".to_string());
    Ok(messages.join("\n"))
}

#[tauri::command]
pub async fn proxy_set_breakpoint(
    state: tauri::State<'_, ProxyState>,
    enabled: bool,
    url_pattern: Option<String>,
) -> Result<(), String> {
    state.inner.breakpoint_enabled.store(enabled, Ordering::Release);
    *state.inner.breakpoint_url_pattern.lock().unwrap() = url_pattern;
    Ok(())
}

#[tauri::command]
pub async fn proxy_continue(
    state: tauri::State<'_, ProxyState>,
    request_id: String,
    action: serde_json::Value,
) -> Result<(), String> {
    let mut breakpoints = state.inner.pending_breakpoints.lock().unwrap();
    if let Some(tx) = breakpoints.remove(&request_id) {
        tx.send(action).map_err(|_| "Breakpoint channel closed".to_string())?;
    }
    Ok(())
}

#[tauri::command]
pub async fn proxy_add_rewrite_rule(
    state: tauri::State<'_, ProxyState>,
    rule: RewriteRule,
) -> Result<(), String> {
    state.inner.rewrite_rules.lock().unwrap().push(rule);
    Ok(())
}

#[tauri::command]
pub async fn proxy_remove_rewrite_rule(
    state: tauri::State<'_, ProxyState>,
    rule_id: String,
) -> Result<(), String> {
    state.inner.rewrite_rules.lock().unwrap().retain(|r| r.id != rule_id);
    Ok(())
}

#[tauri::command]
pub async fn proxy_update_rewrite_rule(
    state: tauri::State<'_, ProxyState>,
    rule: RewriteRule,
) -> Result<(), String> {
    let mut rules = state.inner.rewrite_rules.lock().unwrap();
    if let Some(existing) = rules.iter_mut().find(|r| r.id == rule.id) {
        *existing = rule;
    }
    Ok(())
}

#[tauri::command]
pub async fn proxy_clear_rewrite_rules(
    state: tauri::State<'_, ProxyState>,
) -> Result<(), String> {
    state.inner.rewrite_rules.lock().unwrap().clear();
    Ok(())
}

#[tauri::command]
pub async fn proxy_get_captured(
    state: tauri::State<'_, ProxyState>,
    clear: bool,
) -> Result<Vec<CapturedRequest>, String> {
    let mut captured = state.inner.captured_requests.lock().unwrap();
    let result = captured.clone();
    if clear {
        captured.clear();
    }
    Ok(result)
}

#[tauri::command]
pub async fn proxy_get_status(
    state: tauri::State<'_, ProxyState>,
) -> Result<serde_json::Value, String> {
    let inner = &state.inner;
    Ok(serde_json::json!({
        "running": inner.running.load(Ordering::Acquire),
        "port": *inner.port.lock().unwrap(),
        "breakpoint_enabled": inner.breakpoint_enabled.load(Ordering::Acquire),
        "captured_count": inner.captured_requests.lock().unwrap().len(),
    }))
}

#[tauri::command]
pub async fn proxy_get_ca_cert(
    state: tauri::State<'_, ProxyState>,
) -> Result<Option<String>, String> {
    Ok(state.inner.ca_cert_pem.lock().unwrap().clone())
}

#[tauri::command]
pub async fn proxy_set_device_proxy(
    serial: String,
    port: u16,
) -> Result<String, String> {
    let host = get_local_ip()?;
    let sp_serial = serial.clone();
    let sp_host = host.clone();
    let result = tokio::task::spawn_blocking(move || {
        crate::adb::shell_command(&sp_serial, &format!(
            "settings put global http_proxy {}:{}", sp_host, port
        ))
    }).await.map_err(|e| e.to_string())?;
    match result {
        Ok(_) => Ok(format!("Proxy set to {}:{} on device {}", host, port, serial)),
        Err(e) => Err(format!("Failed to set proxy: {}", e)),
    }
}

#[tauri::command]
pub async fn proxy_clear_device_proxy(
    serial: String,
) -> Result<String, String> {
    let sp_serial = serial.clone();
    let result = tokio::task::spawn_blocking(move || {
        crate::adb::shell_command(&sp_serial, "settings put global http_proxy :0")
    }).await.map_err(|e| e.to_string())?;
    match result {
        Ok(_) => Ok(format!("Proxy cleared on device {}", serial)),
        Err(e) => Err(format!("Failed to clear proxy: {}", e)),
    }
}

/// 尝试 root 设备、remount 系统分区、安装系统 CA 证书。
/// 返回 true 表示证书已成功安装到 /system/etc/security/cacerts/。
async fn try_install_system_cert(serial: &str, cert_pem: &str, app: &tauri::AppHandle) -> bool {
    let root_result = tokio::task::spawn_blocking({
        let s = serial.to_string();
        move || crate::adb::root_device(&s)
    }).await;

    let root_ok = match &root_result {
        Ok(Ok(ref out)) => out.contains("already root")
            || out.contains("running as root")
            || out.contains("restarting adbd")
            || out.trim().is_empty(),
        _ => false,
    };

    if !root_ok {
        app.emit("proxy:debug", "[proxy] adb root 失败，跳过系统证书安装").ok();
        return false;
    }

    app.emit("proxy:debug", "[proxy] 设备已获取 root 权限").ok();

    // adb root 后 adbd 会重启，等一会
    std::thread::sleep(std::time::Duration::from_secs(2));

    let remount_result = tokio::task::spawn_blocking({
        let s = serial.to_string();
        move || crate::adb::remount_device(&s)
    }).await;

    let remount_ok = match remount_result {
        Ok(Ok(ref msg)) => msg.contains("remount succeeded")
            || msg.contains("remount of")
            || msg.trim().is_empty(),
        _ => false,
    };

    if !remount_ok {
        // 尝试 disable-verity 后再 remount
        app.emit("proxy:debug", "[proxy] remount 失败，尝试 disable-verity...").ok();
        let dis_serial = serial.to_string();
        let _ = tokio::task::spawn_blocking(move || {
            crate::adb::shell_command(&dis_serial, "avbctl disable-verification")
        }).await;
        std::thread::sleep(std::time::Duration::from_secs(1));

        // retry remount
        let remount_serial2 = serial.to_string();
        let remount2 = tokio::task::spawn_blocking(move || {
            crate::adb::remount_device(&remount_serial2)
        }).await;

        let remount_ok2 = match remount2 {
            Ok(Ok(ref msg)) => msg.contains("remount succeeded")
                || msg.contains("remount of")
                || msg.trim().is_empty(),
            _ => false,
        };

        if !remount_ok2 {
            app.emit("proxy:debug", "[proxy] 无法 remount 系统分区").ok();
            return false;
        }
    }

    app.emit("proxy:debug", "[proxy] 系统分区可写，安装证书...").ok();

    let hashes = match compute_cert_hashes(cert_pem) {
        Ok(h) => h,
        Err(_) => return false,
    };
    let (md5_hash, sha256_hash) = hashes;

    let install_result = tokio::task::spawn_blocking({
        let s = serial.to_string();
        let md5 = md5_hash.clone();
        let sha256 = sha256_hash.clone();
        move || install_system_cert(&s, &md5, &sha256)
    }).await;

    match install_result {
        Ok(Ok(_)) => {
            app.emit("proxy:debug", "[proxy] 系统证书安装成功").ok();
            true
        }
        _ => false,
    }
}

/// Returns (md5_hash, sha256_hash) for the certificate subject.
/// Android 7-9 uses the MD5-based hash (subject_hash_old).
/// Android 10+ uses SHA-256-based hash (subject_hash in Conscrypt/BoringSSL).
fn compute_cert_hashes(cert_pem: &str) -> Result<(String, String), String> {
    use md5::{Md5, Digest};
    use sha2::Sha256;
    let pem_data = pem::parse(cert_pem).map_err(|e| format!("PEM parse error: {}", e))?;
    let pem_bytes = pem_data.contents();
    let (_, cert) = x509_parser::parse_x509_certificate(pem_bytes)
        .map_err(|e| format!("X509 parse error: {}", e))?;
    let subject_raw = cert.subject().as_raw();

    let mut md5 = Md5::new();
    md5.update(subject_raw);
    let md5_hash = md5.finalize();
    let md5_value = u32::from_le_bytes([md5_hash[0], md5_hash[1], md5_hash[2], md5_hash[3]]);

    let mut sha256 = Sha256::new();
    sha256.update(subject_raw);
    let sha256_hash = sha256.finalize();
    let sha256_value = u32::from_le_bytes([sha256_hash[0], sha256_hash[1], sha256_hash[2], sha256_hash[3]]);

    Ok((format!("{:08x}", md5_value), format!("{:08x}", sha256_value)))
}

fn adb_shell_blocking(serial: &str, cmd: &str) -> Result<String, String> {
    crate::adb::shell_command(serial, cmd)
}

/// Install the CA certificate as a system cert.
/// Tries both MD5 hash (Android 7-9) and SHA-256 hash (Android 10+).
/// Returns the successfully installed hash, or an error if both fail.
fn install_system_cert(serial: &str, md5_hash: &str, sha256_hash: &str) -> Result<String, String> {
    let cert_src = "/sdcard/testspace-ca-cert.pem";
    let mut last_err = String::new();

    for hash in [md5_hash, sha256_hash] {
        let cert_dst = format!("/system/etc/security/cacerts/{}.0", hash);
        let result = (|| -> Result<(), String> {
            adb_shell_blocking(serial, &format!("cat {} > {}", cert_src, cert_dst))?;
            adb_shell_blocking(serial, &format!("chmod 644 {}", cert_dst))?;
            let selinux = adb_shell_blocking(serial, "selinuxenabled 2>/dev/null && echo yes || echo no");
            if selinux.as_ref().map(|s| s.trim() == "yes").unwrap_or(false) {
                let _ = adb_shell_blocking(serial, &format!("chcon u:object_r:system_file:s0 {}", cert_dst));
            }
            Ok(())
        })();
        match result {
            Ok(()) => return Ok(hash.to_string()),
            Err(e) => last_err = e,
        }
    }
    Err(format!("Both MD5 and SHA256 cert installation failed. Last error: {}", last_err))
}

#[tauri::command]
pub async fn proxy_install_cert(
    state: tauri::State<'_, ProxyState>,
    serial: String,
) -> Result<String, String> {
    let cert_pem = state.inner.ca_cert_pem.lock().unwrap().clone()
        .ok_or_else(|| "CA certificate not generated yet. Start the proxy first.".to_string())?;

    let tmp_dir = std::env::temp_dir();
    let cert_path = tmp_dir.join("testspace-ca-cert.pem");
    std::fs::write(&cert_path, &cert_pem)
        .map_err(|e| format!("Failed to write cert: {}", e))?;

    let push_result = tokio::task::spawn_blocking({
        let serial = serial.clone();
        let cp = cert_path.to_string_lossy().to_string();
        move || crate::adb::push_file(&serial, &cp, "/sdcard/testspace-ca-cert.pem")
    }).await.map_err(|e| e.to_string())?;
    push_result?;

    let root_result = tokio::task::spawn_blocking({
        let serial = serial.clone();
        move || crate::adb::root_device(&serial)
    }).await.map_err(|e| e.to_string())?;

    let root_output = root_result?;
    if root_output.contains("already root") || root_output.contains("running as root") || root_output.contains("restarting adbd") || root_output.trim().is_empty() {
        let remount_result = tokio::task::spawn_blocking({
            let serial = serial.clone();
            move || crate::adb::remount_device(&serial)
        }).await.map_err(|e| e.to_string())?;

        let (md5_hash, sha256_hash) = compute_cert_hashes(&cert_pem)?;

        if remount_result.as_ref().map(|s| s.contains("remount succeeded")).unwrap_or(false) {
            let install_serial = serial.clone();
            let md5 = md5_hash.clone();
            let sha256 = sha256_hash.clone();
            let install_result = tokio::task::spawn_blocking(move || {
                install_system_cert(&install_serial, &md5, &sha256)
            }).await.map_err(|e| e.to_string())?;

            match install_result {
                Ok(used_hash) => {
                    Ok(format!(
                        "✅ Certificate installed successfully!\n\n\
                         Location: /system/etc/security/cacerts/{}.0\n\n\
                         A reboot is recommended for the certificate to take effect.\n\
                         Run 'adb reboot' to complete installation.\n\
                         Note: Some apps may not trust the certificate until reboot.",
                        used_hash
                    ))
                }
                Err(e) => {
                    Ok(format!(
                        "Certificate pushed to /sdcard/testspace-ca-cert.pem\n\
                         Remount succeeded, but auto-install failed: {}\n\n\
                         Manual steps:\n\
                         1. adb shell cat /sdcard/testspace-ca-cert.pem > /system/etc/security/cacerts/{}.0\n\
                         2. adb shell chmod 644 /system/etc/security/cacerts/{}.0\n\
                         3. adb reboot",
                        e, md5_hash, md5_hash
                    ))
                }
            }
        } else {
            Ok(format!(
                "Certificate pushed to /sdcard/testspace-ca-cert.pem\n\
                 \n⚠️ REMOUNT FAILED\n\
                 adb remount failed. To install system certificate:\n\n\
                 Option A (disable AVB verification):\n\
                 1. adb shell avbctl disable-verification\n\
                 2. adb reboot\n\
                 3. adb root && adb remount\n\
                 4. adb shell cat /sdcard/testspace-ca-cert.pem > /system/etc/security/cacerts/{}.0\n\
                 5. adb shell chmod 644 /system/etc/security/cacerts/{}.0\n\
                 6. adb reboot\n\n\
                 Option B (user cert - limited trust):\n\
                 Settings → Security → Install from storage → select /sdcard/testspace-ca-cert.pem\n\
                 (Most Android 7+ apps will NOT trust user certificates)",
                md5_hash, sha256_hash
            ))
        }
    } else {
        // Try multiple methods to launch the cert installer, in case one doesn't work
        let cert_intents = [
            // Method 1: Copy to Download first (more accessible on Android 10+)
            format!(
                "cp /sdcard/testspace-ca-cert.pem /sdcard/Download/ 2>/dev/null; \
                 am start -n com.android.certinstaller/.CertInstallerMain \
                 -a android.intent.action.VIEW \
                 -t application/x-x509-ca-cert \
                 -d file:///sdcard/Download/testspace-ca-cert.pem"
            ),
            // Method 2: Fall back to /sdcard/ root
            format!(
                "am start -n com.android.certinstaller/.CertInstallerMain \
                 -a android.intent.action.VIEW \
                 -t application/x-x509-ca-cert \
                 -d file:///sdcard/testspace-ca-cert.pem"
            ),
            // Method 3: Use Settings Security intent
            "am start -a android.settings.SECURITY_SETTINGS".to_string(),
        ];

        let mut cert_launched = false;
        for intent in &cert_intents {
            let sp_serial = serial.clone();
            let cmd = intent.clone();
            if let Ok(result) = tokio::task::spawn_blocking(move || {
                crate::adb::shell_command(&sp_serial, &cmd)
            }).await.map_err(|e| e.to_string()).and_then(|r| r) {
                if !result.contains("Error") && !result.contains("not found") {
                    cert_launched = true;
                    break;
                }
            }
        }

        if cert_launched {
            Ok("Certificate pushed to /sdcard/testspace-ca-cert.pem\n\
                Cert installer launched on device.\n\
                ⚠️ User certificate - only apps that trust user certs will work.\n\
                For full HTTPS interception (all apps), root + system cert required.\n\
                Check device screen and enter a certificate name to install.".to_string())
        } else {
            Ok("Certificate pushed to /sdcard/testspace-ca-cert.pem\n\
                ⚠️ Could not auto-launch cert installer on device.\n\
                Please manually install:\n\
                1. Settings → Security → Install from storage\n\
                2. Select /sdcard/testspace-ca-cert.pem\n\
                ⚠️ User certificates only work with apps that explicitly trust them.\n\
                For full HTTPS interception, root + system cert is required.".to_string())
        }
    }
}

#[tauri::command]
pub async fn proxy_replay(
    captured: CapturedRequest,
) -> Result<CapturedRequest, String> {
    let start_time = get_timestamp();
    let url_str = &captured.url;
    let uri: http_mitm_proxy::hyper::http::Uri = url_str.parse()
        .map_err(|e| format!("Invalid URL: {}", e))?;

    let mut builder = Request::builder()
        .method(captured.method.as_str())
        .uri(&uri);

    for h in &captured.request_headers {
        if h.len() >= 2 {
            if let (Ok(name), Ok(value)) = (
                http_mitm_proxy::hyper::http::HeaderName::from_bytes(h[0].as_bytes()),
                http_mitm_proxy::hyper::http::HeaderValue::from_str(&h[1]),
            ) {
                builder = builder.header(name, value);
            }
        }
    }

    let body_str = captured.request_body.clone().unwrap_or_default();
    let req = builder.body(box_body(Bytes::from(body_str)))
        .map_err(|e| format!("Cannot build request: {}", e))?;

    let client = DefaultClient::new();
    let (res_parts, res_body) = client.send_request(req).await
        .map_err(|e| format!("Request failed: {}", e))?
        .0.into_parts();

    let end_time = get_timestamp();
    let duration = ((end_time - start_time) * 1000.0 * 100.0).round() / 100.0;
    let res_body_bytes = read_body_bytes(res_body).await;
    let res_body_str = if res_body_bytes.is_empty() { None } else { String::from_utf8(res_body_bytes.to_vec()).ok() };

    Ok(CapturedRequest {
        id: Uuid::new_v4().to_string(),
        response_status_code: Some(res_parts.status.as_u16()),
        response_status_text: Some(res_parts.status.canonical_reason().unwrap_or("Unknown").to_string()),
        response_headers: Some(headers_to_vec(&res_parts.headers)),
        response_body: res_body_str,
        end_time: Some(end_time),
        duration: Some(duration),
        response_size: res_body_bytes.len() as u64,
        ..captured
    })
}
