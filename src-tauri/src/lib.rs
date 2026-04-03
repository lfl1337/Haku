use tauri::Manager;
use std::process::Command;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let resource_path = app.path().resource_dir()
                .expect("failed to resolve resource dir");

            std::thread::spawn(move || {
                Command::new("python")
                    .args(["-u", "backend/main.py"])
                    .current_dir(&resource_path)
                    .spawn()
                    .expect("Failed to start backend");
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Haku");
}
