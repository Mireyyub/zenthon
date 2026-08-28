//! Leon desktop shell seed (Phase 10).
//!
//! INTENT: window / process orchestration only.
//! FORBIDDEN: AI reasoning, tool execution, unrestricted FS.
//!
//! Full Tauri integration requires `tauri` crate + CLI.
//! This binary is a *compile-light* seed that documents the boundary:
//! print supervisor instructions and exit 0.
//!
//! When wiring real Tauri:
//! - `tauri::Builder` + webview → http://127.0.0.1:5173 or ui/dist
//! - sidecar or `Command` to run `python -m core.supervisor`
//! - never import cognitive Python into Rust

use serde::Serialize;

#[derive(Serialize)]
struct SeedStatus {
    product: &'static str,
    phase: &'static str,
    role: &'static str,
    ai_in_rust: bool,
    supervisor: &'static str,
    ui_dev: &'static str,
    api: &'static str,
    note: &'static str,
}

fn main() {
    let status = SeedStatus {
        product: "Leon",
        phase: "10",
        role: "desktop-shell-seed",
        ai_in_rust: false,
        supervisor: "python -m core.supervisor",
        ui_dev: "http://127.0.0.1:5173",
        api: "http://127.0.0.1:8000/api/v1",
        note: "Replace this seed with tauri::Builder when Rust toolchain + tauri-cli are installed. No reasoning here.",
    };
    println!("{}", serde_json::to_string_pretty(&status).unwrap());
}
