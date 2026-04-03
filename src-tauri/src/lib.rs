use tauri::Manager;
use std::process::Command;
use std::path::PathBuf;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let backend_dir: PathBuf = if cfg!(debug_assertions) {
                // Dev: cwd is src-tauri/, project root is one level up
                let mut dir = std::env::current_dir()
                    .expect("failed to get cwd");
                // If we're inside src-tauri, go up one level
                if dir.ends_with("src-tauri") {
                    dir.pop();
                }
                dir
            } else {
                // Production: resources bundled relative to resource_dir
                app.path().resource_dir()
                    .expect("failed to resolve resource dir")
            };

            println!("[Haku] Starting backend from: {:?}", backend_dir);

            std::thread::spawn(move || {
                let child = Command::new("python")
                    .args(["-u", "backend/main.py"])
                    .current_dir(&backend_dir)
                    .spawn();

                match child {
                    Ok(_) => println!("[Haku] Backend started"),
                    Err(e) => eprintln!("[Haku] Failed to start backend: {}", e),
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Haku");
}
