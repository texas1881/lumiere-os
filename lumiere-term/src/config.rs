// ╔══════════════════════════════════════════════════════════════╗
// ║          ✦ Lumière Terminal — Configuration                  ║
// ╚══════════════════════════════════════════════════════════════╝

use serde::Deserialize;
use std::path::PathBuf;

/// Lumière Terminal konfigürasyonu (TOML tabanlı).
#[derive(Debug, Deserialize)]
pub struct Config {
    #[serde(default = "default_font_family")]
    pub font_family: String,

    #[serde(default = "default_font_size")]
    pub font_size: f32,

    #[serde(default = "default_opacity")]
    pub opacity: f32,

    #[serde(default = "default_padding")]
    pub padding: u32,

    #[serde(default = "default_columns")]
    pub columns: u16,

    #[serde(default = "default_rows")]
    pub rows: u16,

    #[serde(default = "default_window_width")]
    pub window_width: u32,

    #[serde(default = "default_window_height")]
    pub window_height: u32,

    #[serde(default = "default_scrollback")]
    pub scrollback_lines: usize,

    #[serde(default)]
    pub colors: ColorConfig,
}

/// Lumière koyu tema renk paleti.
#[derive(Debug, Deserialize)]
pub struct ColorConfig {
    #[serde(default = "default_bg")]
    pub background: [f32; 4],

    #[serde(default = "default_fg")]
    pub foreground: [f32; 4],

    #[serde(default = "default_cursor_color")]
    pub cursor: [f32; 4],

    #[serde(default = "default_selection")]
    pub selection: [f32; 4],

    #[serde(default = "default_palette")]
    pub palette: [[f32; 3]; 16],
}

impl Default for ColorConfig {
    fn default() -> Self {
        Self {
            background: default_bg(),
            foreground: default_fg(),
            cursor: default_cursor_color(),
            selection: default_selection(),
            palette: default_palette(),
        }
    }
}

// ── Varsayılan Değerler ─────────────────────────────────────────

fn default_font_family() -> String { "JetBrains Mono".into() }
fn default_font_size() -> f32 { 13.0 }
fn default_opacity() -> f32 { 0.95 }
fn default_padding() -> u32 { 8 }
fn default_columns() -> u16 { 80 }
fn default_rows() -> u16 { 24 }
fn default_window_width() -> u32 { 900 }
fn default_window_height() -> u32 { 600 }
fn default_scrollback() -> usize { 10_000 }

// Lumière koyu tema renkleri
fn default_bg() -> [f32; 4] { [0.051, 0.051, 0.078, 0.95] }   // #0D0D14
fn default_fg() -> [f32; 4] { [0.910, 0.902, 0.941, 1.0] }    // #E8E6F0
fn default_cursor_color() -> [f32; 4] { [0.961, 0.651, 0.137, 1.0] } // #F5A623
fn default_selection() -> [f32; 4] { [0.961, 0.651, 0.137, 0.3] }

fn default_palette() -> [[f32; 3]; 16] {
    [
        // Normal
        [0.102, 0.102, 0.180],   // #1A1A2E  black
        [0.973, 0.443, 0.443],   // #F87171  red
        [0.290, 0.871, 0.502],   // #4ADE80  green
        [0.961, 0.651, 0.137],   // #F5A623  yellow  (gold)
        [0.376, 0.647, 0.980],   // #60A5FA  blue
        [0.647, 0.361, 0.965],   // #A55CF6  magenta
        [0.133, 0.827, 0.933],   // #22D3EE  cyan
        [0.910, 0.902, 0.941],   // #E8E6F0  white
        // Bright
        [0.420, 0.408, 0.502],   // #6B6880  bright black
        [1.000, 0.490, 0.490],   // #FF7D7D  bright red
        [0.400, 0.941, 0.600],   // #66F099  bright green
        [1.000, 0.816, 0.502],   // #FFD080  bright yellow
        [0.525, 0.757, 1.000],   // #86C1FF  bright blue
        [0.757, 0.557, 1.000],   // #C18EFF  bright magenta
        [0.290, 0.902, 0.984],   // #4AE6FB  bright cyan
        [1.000, 1.000, 1.000],   // #FFFFFF  bright white
    ]
}

impl Config {
    /// Konfigürasyon dosyasını yükle.
    pub fn load() -> Self {
        let path = Self::config_path();

        if path.exists() {
            match std::fs::read_to_string(&path) {
                Ok(content) => match toml::from_str(&content) {
                    Ok(config) => return config,
                    Err(e) => log::warn!("Konfigürasyon parse hatası: {e}"),
                },
                Err(e) => log::warn!("Konfigürasyon okunamadı: {e}"),
            }
        }

        Self::default()
    }

    fn config_path() -> PathBuf {
        dirs::config_dir()
            .unwrap_or_else(|| PathBuf::from("~/.config"))
            .join("lumiere")
            .join("terminal.toml")
    }
}

impl Default for Config {
    fn default() -> Self {
        Self {
            font_family: default_font_family(),
            font_size: default_font_size(),
            opacity: default_opacity(),
            padding: default_padding(),
            columns: default_columns(),
            rows: default_rows(),
            window_width: default_window_width(),
            window_height: default_window_height(),
            scrollback_lines: default_scrollback(),
            colors: ColorConfig::default(),
        }
    }
}
