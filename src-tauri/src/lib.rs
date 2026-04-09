use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use std::sync::Mutex;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::PathBuf;

struct BackendProcess(Mutex<Option<tauri_plugin_shell::process::CommandChild>>);

fn log_path() -> PathBuf {
    let appdata = std::env::var("APPDATA").unwrap_or_else(|_| "C:\\Temp".to_string());
    let dir = PathBuf::from(appdata).join("Haku");
    let _ = std::fs::create_dir_all(&dir);
    dir.join("haku.log")
}

fn log(msg: &str) {
    let path = log_path();
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(&path) {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        let _ = writeln!(f, "[{}] {}", now, msg);
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let path = log_path();
    let _ = std::fs::write(&path, "");
    log(&format!("Haku starting — log: {}", path.display()));
    log(&format!("exe: {}", std::env::current_exe().map(|p| p.display().to_string()).unwrap_or_else(|_| "?".into())));
    log(&format!("cwd: {}", std::env::current_dir().map(|p| p.display().to_string()).unwrap_or_else(|_| "?".into())));

    // List install directory so we can verify sidecar is present
    if let Ok(entries) = std::fs::read_dir(std::env::current_dir().unwrap_or_default()) {
        let files: Vec<String> = entries
            .filter_map(|e| e.ok().map(|e| e.file_name().to_string_lossy().to_string()))
            .collect();
        log(&format!("install dir contents: {:?}", files));
    }

    log("Building Tauri app...");
    let app = match tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            log("setup() start");

            let resource_dir = app.path().resource_dir()
                .map(|p| p.display().to_string())
                .unwrap_or_else(|_| "?".into());
            log(&format!("resource_dir: {}", resource_dir));

            log("Creating sidecar...");
            let sidecar = match app.shell().sidecar("backend") {
                Ok(s) => { log("Sidecar command OK"); s }
                Err(e) => {
                    log(&format!("ERROR: sidecar() failed: {}", e));
                    return Err(format!("Backend nicht gefunden: {}", e).into());
                }
            };

            log("Spawning sidecar...");
            let (mut rx, child) = match sidecar.spawn() {
                Ok(r) => { log("Sidecar spawned OK"); r }
                Err(e) => {
                    log(&format!("ERROR: spawn() failed: {}", e));
                    return Err(format!("Backend konnte nicht gestartet werden: {}", e).into());
                }
            };

            tauri::async_runtime::spawn(async move {
                use tauri_plugin_shell::process::CommandEvent;
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            log(&format!("[backend] {}", String::from_utf8_lossy(&line).trim_end()));
                        }
                        CommandEvent::Stderr(line) => {
                            log(&format!("[backend:err] {}", String::from_utf8_lossy(&line).trim_end()));
                        }
                        CommandEvent::Error(e) => {
                            log(&format!("[backend:error] {}", e));
                        }
                        CommandEvent::Terminated(s) => {
                            log(&format!("[backend:terminated] code={:?}", s.code));
                        }
                        _ => {}
                    }
                }
            });

            let state = app.state::<BackendProcess>();
            *state.0.lock().unwrap() = Some(child);

            log("setup() done");
            Ok(())
        })
        .build(tauri::generate_context!())
    {
        Ok(a) => { log("App built OK — starting event loop"); a }
        Err(e) => {
            log(&format!("FATAL: build() failed: {}", e));
            return;
        }
    };

    app.run(|app_handle, event| {
        match event {
            tauri::RunEvent::Exit => {
                log("RunEvent::Exit");
                let state = app_handle.state::<BackendProcess>();
                let child = state.0.lock().unwrap().take();
                if let Some(child) = child {
                    let _ = child.kill();
                    log("Backend killed on exit");
                }
            }
            tauri::RunEvent::WindowEvent { event: tauri::WindowEvent::Destroyed, .. } => {
                log("Window destroyed");
            }
            _ => {}
        }
    });
}
