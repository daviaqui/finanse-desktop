#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use rand::RngCore;
use serde::Serialize;
use serde_json::{json, Value};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Mutex,
};
use std::time::Duration;
use tauri::{Manager, State};
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

#[derive(Clone, Serialize)]
struct BackendStatus {
    state: String,
    message: String,
}
struct Backend {
    status: Mutex<BackendStatus>,
    child: Mutex<Option<CommandChild>>,
    port: Mutex<Option<u16>>,
    token: String,
    stopping: AtomicBool,
    client: reqwest::Client,
    maintenance: tokio::sync::Mutex<()>,
}
impl Backend {
    fn set_status(&self, state: &str, message: &str) {
        *self.status.lock().unwrap() = BackendStatus {
            state: state.into(),
            message: message.into(),
        };
    }
    fn stop(&self) {
        if let Some(mut child) = self.child.lock().unwrap().take() {
            let _ = child.write(b"shutdown\n");
            // Give SQLite/uvicorn a bounded graceful shutdown before forcing exit.
            std::thread::spawn(move || {
                std::thread::sleep(Duration::from_secs(7));
                let _ = child.kill();
            });
        }
    }
}

#[tauri::command]
fn backend_status(backend: State<Backend>) -> BackendStatus {
    backend.status.lock().unwrap().clone()
}
#[tauri::command]
fn data_directory(app: tauri::AppHandle) -> Result<String, String> {
    app.path()
        .app_data_dir()
        .map(|p| p.to_string_lossy().into_owned())
        .map_err(|e| e.to_string())
}

async fn request(
    backend: &Backend,
    method: &str,
    path: &str,
    body: Value,
) -> Result<Value, String> {
    let port = backend
        .port
        .lock()
        .unwrap()
        .ok_or("O serviço local ainda não está disponível")?;
    let method = reqwest::Method::from_bytes(method.as_bytes()).map_err(|e| e.to_string())?;
    let mut request = backend
        .client
        .request(method, format!("http://127.0.0.1:{port}{path}"))
        .bearer_auth(&backend.token);
    if !body.is_null() {
        request = request.json(&body);
    }
    let response = request.send().await.map_err(|_| {
        "Não foi possível acessar o serviço local. Feche e abra o aplicativo novamente.".to_string()
    })?;
    let status = response.status().as_u16();
    let data = if status == 204 {
        Value::Null
    } else {
        response.json::<Value>().await.map_err(|e| e.to_string())?
    };
    Ok(json!({"status": status, "data": data}))
}

fn allowed_api(method: &str, path: &str) -> bool {
    if !matches!(method, "GET" | "POST" | "PUT" | "PATCH" | "DELETE") {
        return false;
    }
    let route = path.split('?').next().unwrap_or("");
    let parts: Vec<_> = route.split('/').collect();
    if parts.len() < 4 || parts[..3] != ["", "api", "v1"] {
        return false;
    }
    match parts[3] {
        "dashboard" => parts.len() == 4 && method == "GET",
        "transactions" | "categories" => {
            if parts.len() == 4 {
                return matches!(method, "GET" | "POST");
            }
            parts.len() == 5
                && parts[4].len() == 36
                && parts[4].chars().all(|c| c.is_ascii_hexdigit() || c == '-')
        }
        _ => false,
    }
}

#[tauri::command]
async fn api_request(
    backend: State<'_, Backend>,
    method: String,
    path: String,
    body: Value,
) -> Result<Value, String> {
    if !allowed_api(&method, &path) {
        return Err("Operação não permitida".into());
    }
    request(&backend, &method, &path, body).await
}

async fn selected_file(app: tauri::AppHandle, restore: bool) -> Result<Option<String>, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let dialog = app.dialog().file().add_filter("Backup Finanse", &["sqlite3"]);
        let file = if restore {
            dialog.set_title("Restaurar backup do Finanse").blocking_pick_file()
        } else {
            dialog.set_title("Salvar backup do Finanse").set_file_name("finanse-backup.sqlite3").blocking_save_file()
        };
        let Some(file) = file else { return Ok(None); };
        let path = file.into_path().map_err(|e| e.to_string())?;
        if restore || path.exists() {
            let message = if restore { "Substituir todos os dados atuais por este backup? Uma cópia dos dados atuais será preservada." }
                else { "Este arquivo já existe. Substituir o backup anterior?" };
            if !app.dialog().message(message).title("Confirmar substituição")
                .buttons(MessageDialogButtons::OkCancelCustom("Substituir".into(), "Cancelar".into())).blocking_show() {
                return Ok(None);
            }
        }
        Ok(Some(path.to_string_lossy().into_owned()))
    }).await.map_err(|e| e.to_string())?
}
async fn maintenance(
    app: tauri::AppHandle,
    backend: &Backend,
    restore: bool,
) -> Result<Option<String>, String> {
    let _guard = backend
        .maintenance
        .try_lock()
        .map_err(|_| "Outra operação de backup está em andamento")?;
    let Some(path) = selected_file(app, restore).await? else {
        return Ok(None);
    };
    let route = if restore { "restore" } else { "backup" };
    let result = request(
        backend,
        "POST",
        &format!("/api/v1/maintenance/{route}"),
        json!({"path": path, "confirmed": true}),
    )
    .await?;
    if result["status"].as_u64().unwrap_or(500) >= 400 {
        return Err(result["data"]["detail"]
            .as_str()
            .unwrap_or("Falha ao processar backup")
            .into());
    }
    Ok(Some(
        result["data"]["message"]
            .as_str()
            .unwrap_or("Operação concluída")
            .into(),
    ))
}
#[tauri::command]
async fn backup_data(
    app: tauri::AppHandle,
    backend: State<'_, Backend>,
) -> Result<Option<String>, String> {
    maintenance(app, &backend, false).await
}
#[tauri::command]
async fn restore_data(
    app: tauri::AppHandle,
    backend: State<'_, Backend>,
) -> Result<Option<String>, String> {
    maintenance(app, &backend, true).await
}

fn start_backend(app: &tauri::AppHandle) -> Result<(), String> {
    let directory = app.path().app_data_dir().map_err(|e| e.to_string())?;
    std::fs::create_dir_all(&directory).map_err(|e| e.to_string())?;
    let (mut receiver, mut child) = app
        .shell()
        .sidecar("finanse-backend")
        .map_err(|e| e.to_string())?
        .spawn()
        .map_err(|e| e.to_string())?;
    let backend = app.state::<Backend>();
    let config = json!({"token": backend.token, "data_dir": directory});
    child
        .write(format!("{config}\n").as_bytes())
        .map_err(|e| e.to_string())?;
    *backend.child.lock().unwrap() = Some(child);
    let handle = app.clone();
    tauri::async_runtime::spawn(async move {
        while let Some(event) = receiver.recv().await {
            let backend = handle.state::<Backend>();
            match event {
                CommandEvent::Stdout(line) => {
                    if let Ok(value) = serde_json::from_slice::<Value>(&line) {
                        match value["event"].as_str() {
                            Some("ready") => {
                                if let Some(port) =
                                    value["port"].as_u64().filter(|p| *p > 0 && *p <= 65535)
                                {
                                    *backend.port.lock().unwrap() = Some(port as u16);
                                    match request(&backend, "GET", "/health", Value::Null).await {
                                        Ok(result) if result["status"] == 200 => {
                                            backend.set_status("ready", "")
                                        }
                                        _ => backend.set_status(
                                            "error",
                                            "O serviço local não respondeu à verificação inicial.",
                                        ),
                                    }
                                }
                            }
                            Some("error") => backend.set_status(
                                "error",
                                value["message"]
                                    .as_str()
                                    .unwrap_or("Falha ao iniciar o banco local"),
                            ),
                            _ => {}
                        }
                    }
                }
                CommandEvent::Terminated(_) | CommandEvent::Error(_) => {
                    *backend.port.lock().unwrap() = None;
                    if backend.status.lock().unwrap().state != "error" {
                        backend.set_status(
                            "error",
                            "O serviço local foi encerrado. Feche e abra o aplicativo novamente.",
                        );
                    }
                    break;
                }
                _ => {}
            }
        }
    });
    let handle = app.clone();
    tauri::async_runtime::spawn(async move {
        tokio::time::sleep(Duration::from_secs(60)).await;
        let backend = handle.state::<Backend>();
        if backend.status.lock().unwrap().state == "loading" {
            backend.set_status("error", "A inicialização demorou mais de 60 segundos. Verifique a pasta de dados e reinicie o aplicativo.");
            backend.stop();
        }
    });
    Ok(())
}

fn main() {
    let mut random = [0u8; 32];
    rand::rngs::OsRng.fill_bytes(&mut random);
    let token: String = random.iter().map(|b| format!("{b:02x}")).collect();
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _, _| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(Backend {
            status: Mutex::new(BackendStatus {
                state: "loading".into(),
                message: "Preparando seu banco de dados local…".into(),
            }),
            child: Mutex::new(None),
            port: Mutex::new(None),
            token,
            stopping: AtomicBool::new(false),
            client: reqwest::Client::builder()
                .no_proxy()
                .redirect(reqwest::redirect::Policy::none())
                .timeout(Duration::from_secs(120))
                .build()
                .expect("HTTP client"),
            maintenance: tokio::sync::Mutex::new(()),
        })
        .invoke_handler(tauri::generate_handler![
            backend_status,
            data_directory,
            api_request,
            backup_data,
            restore_data
        ])
        .setup(|app| {
            if let Err(error) = start_backend(app.handle()) {
                app.state::<Backend>().set_status("error", &error);
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("Não foi possível abrir a janela do FinanSee Desktop");
    app.run(|app, event| {
        if let tauri::RunEvent::ExitRequested { api, .. } = event {
            let backend = app.state::<Backend>();
            if !backend.stopping.swap(true, Ordering::SeqCst) {
                api.prevent_exit();
                backend.stop();
                let handle = app.clone();
                tauri::async_runtime::spawn(async move {
                    // Keep the parent alive while the sidecar flushes and exits.
                    for _ in 0..80 {
                        tokio::time::sleep(Duration::from_millis(100)).await;
                        if handle.state::<Backend>().port.lock().unwrap().is_none() {
                            break;
                        }
                    }
                    handle.exit(0);
                });
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::allowed_api;
    #[test]
    fn native_bridge_rejects_arbitrary_destinations_and_maintenance() {
        assert!(allowed_api("GET", "/api/v1/transactions?search=abc&page=1"));
        assert!(!allowed_api("POST", "/api/v1/maintenance/restore"));
        assert!(!allowed_api("GET", "http://example.com"));
        assert!(!allowed_api(
            "GET",
            "/api/v1/transactions/../maintenance/backup"
        ));
        assert!(!allowed_api(
            "GET",
            "/api/v1/transactions/%2e%2e%2fmaintenance"
        ));
    }
}
