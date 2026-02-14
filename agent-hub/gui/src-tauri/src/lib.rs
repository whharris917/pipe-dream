use std::process::{Command, Stdio};

#[cfg(windows)]
use std::os::windows::process::CommandExt;

/// Spawn `agent-hub start` as a fully detached process that survives GUI exit.
#[tauri::command]
fn spawn_hub() -> Result<(), String> {
    let mut cmd = Command::new("agent-hub");
    cmd.arg("start");

    // Detached/windowless processes have no console, so stdout/stderr are
    // invalid file descriptors.  Redirect to null to prevent the Hub CLI
    // (click.echo) from crashing with OSError: Bad file descriptor.
    cmd.stdout(Stdio::null());
    cmd.stderr(Stdio::null());

    // Detach from parent process group so the Hub survives GUI close.
    #[cfg(windows)]
    {
        const CREATE_NEW_PROCESS_GROUP: u32 = 0x00000200;
        const CREATE_NO_WINDOW: u32 = 0x08000000;
        cmd.creation_flags(CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW);
    }

    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt as UnixCommandExt;
        // setsid creates a new session, fully detaching from the parent.
        unsafe {
            cmd.pre_exec(|| {
                libc::setsid();
                Ok(())
            });
        }
    }

    cmd.spawn().map_err(|e| format!("Failed to spawn agent-hub: {e}"))?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![spawn_hub])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
