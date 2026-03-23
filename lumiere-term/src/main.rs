// ╔══════════════════════════════════════════════════════════════╗
// ║          ✦ Lumière Terminal — Entry Point                    ║
// ╚══════════════════════════════════════════════════════════════╝
//!
//! GPU-hızlandırmalı, Wayland-native terminal emülatörü.
//!
//! Modüller:
//!   - `config`   — TOML konfigürasyon yönetimi
//!   - `pty`      — PTY fork/exec ve I/O
//!   - `terminal` — VTE state machine ve grid buffer
//!   - `renderer` — wgpu GPU rendering pipeline

mod config;
mod pty;
mod renderer;
mod terminal;

use config::Config;
use pty::Pty;
use renderer::Renderer;
use terminal::Terminal;

use crossbeam_channel::{bounded, select};
use log::{error, info};
use winit::{
    dpi::PhysicalSize,
    event::{ElementState, Event, KeyEvent, WindowEvent},
    event_loop::{ControlFlow, EventLoop},
    keyboard::{Key, NamedKey},
    window::WindowBuilder,
};

fn main() {
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info"),
    )
    .init();

    info!("✦ Lumière Terminal v0.3.0");

    // Konfigürasyon yükle
    let config = Config::load();
    info!("Font: {} {}pt", config.font_family, config.font_size);

    // Event loop + pencere
    let event_loop = EventLoop::new().expect("Event loop oluşturulamadı");
    let window = WindowBuilder::new()
        .with_title("✦ Lumière Terminal")
        .with_inner_size(PhysicalSize::new(
            config.window_width,
            config.window_height,
        ))
        .with_transparent(config.opacity < 1.0)
        .build(&event_loop)
        .expect("Pencere oluşturulamadı");

    // GPU renderer
    let mut renderer = pollster::block_on(Renderer::new(&window, &config));

    // Terminal state
    let mut term = Terminal::new(config.columns, config.rows);

    // PTY başlat
    let shell = std::env::var("SHELL").unwrap_or_else(|_| "/bin/zsh".into());
    let (pty_tx, pty_rx) = bounded::<Vec<u8>>(64);
    let mut pty = Pty::spawn(&shell, config.columns, config.rows, pty_tx)
        .expect("PTY oluşturulamadı");

    // ── Ana Döngü ──────────────────────────────────────────────
    event_loop
        .run(move |event, target| {
            target.set_control_flow(ControlFlow::Poll);

            // PTY çıktısını oku
            while let Ok(data) = pty_rx.try_recv() {
                term.process(&data);
            }

            match event {
                Event::WindowEvent { event, .. } => match event {
                    WindowEvent::CloseRequested => {
                        target.exit();
                    }

                    WindowEvent::Resized(size) => {
                        renderer.resize(size.width, size.height);
                        let (cols, rows) = renderer.grid_dimensions();
                        term.resize(cols, rows);
                        pty.resize(cols, rows);
                    }

                    WindowEvent::KeyboardInput {
                        event:
                            KeyEvent {
                                state: ElementState::Pressed,
                                logical_key,
                                text,
                                ..
                            },
                        ..
                    } => {
                        // Metin girişi → PTY
                        if let Some(text) = text {
                            pty.write(text.as_bytes());
                        } else {
                            match logical_key {
                                Key::Named(NamedKey::Enter) => pty.write(b"\r"),
                                Key::Named(NamedKey::Backspace) => pty.write(b"\x7f"),
                                Key::Named(NamedKey::Tab) => pty.write(b"\t"),
                                Key::Named(NamedKey::Escape) => pty.write(b"\x1b"),
                                Key::Named(NamedKey::ArrowUp) => pty.write(b"\x1b[A"),
                                Key::Named(NamedKey::ArrowDown) => pty.write(b"\x1b[B"),
                                Key::Named(NamedKey::ArrowRight) => pty.write(b"\x1b[C"),
                                Key::Named(NamedKey::ArrowLeft) => pty.write(b"\x1b[D"),
                                Key::Named(NamedKey::Home) => pty.write(b"\x1b[H"),
                                Key::Named(NamedKey::End) => pty.write(b"\x1b[F"),
                                Key::Named(NamedKey::PageUp) => pty.write(b"\x1b[5~"),
                                Key::Named(NamedKey::PageDown) => pty.write(b"\x1b[6~"),
                                Key::Named(NamedKey::Delete) => pty.write(b"\x1b[3~"),
                                _ => {}
                            }
                        }
                    }

                    WindowEvent::RedrawRequested => {
                        renderer.render(&term);
                    }

                    _ => {}
                },

                Event::AboutToWait => {
                    window.request_redraw();
                }

                _ => {}
            }
        })
        .expect("Event loop hatası");
}
