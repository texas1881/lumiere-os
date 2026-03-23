// ╔══════════════════════════════════════════════════════════════╗
// ║          ✦ Lumière Terminal — Terminal State Machine         ║
// ╚══════════════════════════════════════════════════════════════╝
//!
//! VTE tabanlı terminal grid ve scrollback buffer yönetimi.

/// Hücre rengi.
#[derive(Clone, Copy, Debug)]
pub struct CellColor {
    pub r: f32,
    pub g: f32,
    pub b: f32,
}

impl Default for CellColor {
    fn default() -> Self {
        Self { r: 0.91, g: 0.902, b: 0.941 } // Lumière fg
    }
}

/// Hücre stilleri.
#[derive(Clone, Copy, Debug, Default)]
pub struct CellStyle {
    pub bold: bool,
    pub italic: bool,
    pub underline: bool,
    pub strikethrough: bool,
    pub inverse: bool,
}

/// Terminal grid hücresi.
#[derive(Clone, Debug)]
pub struct Cell {
    pub ch: char,
    pub fg: CellColor,
    pub bg: CellColor,
    pub style: CellStyle,
}

impl Default for Cell {
    fn default() -> Self {
        Self {
            ch: ' ',
            fg: CellColor::default(),
            bg: CellColor { r: 0.0, g: 0.0, b: 0.0 },
            style: CellStyle::default(),
        }
    }
}

/// Terminal durumu.
pub struct Terminal {
    pub cols: u16,
    pub rows: u16,
    pub grid: Vec<Vec<Cell>>,
    pub scrollback: Vec<Vec<Cell>>,
    pub scrollback_limit: usize,

    // Cursor pozisyonu
    pub cursor_x: u16,
    pub cursor_y: u16,
    pub cursor_visible: bool,

    // Mevcut stiller
    current_fg: CellColor,
    current_bg: CellColor,
    current_style: CellStyle,

    // Escape sekansı İşleme
    esc_state: EscState,
    esc_buf: String,
}

#[derive(Debug, PartialEq)]
enum EscState {
    Normal,
    Escape,
    Csi,
    Osc,
}

impl Terminal {
    pub fn new(cols: u16, rows: u16) -> Self {
        let grid = vec![vec![Cell::default(); cols as usize]; rows as usize];

        Self {
            cols,
            rows,
            grid,
            scrollback: Vec::new(),
            scrollback_limit: 10_000,
            cursor_x: 0,
            cursor_y: 0,
            cursor_visible: true,
            current_fg: CellColor::default(),
            current_bg: CellColor { r: 0.0, g: 0.0, b: 0.0 },
            current_style: CellStyle::default(),
            esc_state: EscState::Normal,
            esc_buf: String::with_capacity(64),
        }
    }

    /// Boyutu değiştir.
    pub fn resize(&mut self, cols: u16, rows: u16) {
        self.cols = cols;
        self.rows = rows;

        // Yeni grid
        let mut new_grid = vec![vec![Cell::default(); cols as usize]; rows as usize];
        for (y, row) in self.grid.iter().enumerate() {
            if y >= rows as usize { break; }
            for (x, cell) in row.iter().enumerate() {
                if x >= cols as usize { break; }
                new_grid[y][x] = cell.clone();
            }
        }
        self.grid = new_grid;

        // Cursor sınırla
        self.cursor_x = self.cursor_x.min(cols - 1);
        self.cursor_y = self.cursor_y.min(rows - 1);
    }

    /// PTY çıktısını işle.
    pub fn process(&mut self, data: &[u8]) {
        for &byte in data {
            self.process_byte(byte);
        }
    }

    fn process_byte(&mut self, byte: u8) {
        match self.esc_state {
            EscState::Normal => self.process_normal(byte),
            EscState::Escape => self.process_escape(byte),
            EscState::Csi => self.process_csi(byte),
            EscState::Osc => self.process_osc(byte),
        }
    }

    fn process_normal(&mut self, byte: u8) {
        match byte {
            0x1b => {
                self.esc_state = EscState::Escape;
                self.esc_buf.clear();
            }
            b'\n' => self.newline(),
            b'\r' => self.cursor_x = 0,
            b'\t' => {
                let tab_stop = ((self.cursor_x / 8) + 1) * 8;
                self.cursor_x = tab_stop.min(self.cols - 1);
            }
            0x08 => {
                // Backspace
                if self.cursor_x > 0 {
                    self.cursor_x -= 1;
                }
            }
            0x07 => {
                // Bell — yoksay
            }
            0x20..=0x7e | 0x80.. => {
                // Yazdırılabilir karakter
                self.put_char(byte as char);
            }
            _ => {}
        }
    }

    fn process_escape(&mut self, byte: u8) {
        match byte {
            b'[' => {
                self.esc_state = EscState::Csi;
                self.esc_buf.clear();
            }
            b']' => {
                self.esc_state = EscState::Osc;
                self.esc_buf.clear();
            }
            b'(' | b')' | b'*' | b'+' => {
                // Charset designation — yoksay
                self.esc_state = EscState::Normal;
            }
            b'M' => {
                // Reverse index
                if self.cursor_y > 0 {
                    self.cursor_y -= 1;
                }
                self.esc_state = EscState::Normal;
            }
            b'c' => {
                // Full reset
                *self = Self::new(self.cols, self.rows);
            }
            _ => {
                self.esc_state = EscState::Normal;
            }
        }
    }

    fn process_csi(&mut self, byte: u8) {
        match byte {
            0x30..=0x3f => {
                self.esc_buf.push(byte as char);
            }
            0x20..=0x2f => {
                self.esc_buf.push(byte as char);
            }
            0x40..=0x7e => {
                self.esc_buf.push(byte as char);
                self.execute_csi();
                self.esc_state = EscState::Normal;
            }
            _ => {
                self.esc_state = EscState::Normal;
            }
        }
    }

    fn process_osc(&mut self, byte: u8) {
        match byte {
            0x07 => {
                // BEL — OSC bitir
                self.esc_state = EscState::Normal;
            }
            0x1b => {
                // ESC — ST başlangıcı olabilir
                self.esc_state = EscState::Normal;
            }
            _ => {
                self.esc_buf.push(byte as char);
            }
        }
    }

    fn execute_csi(&mut self) {
        let seq = &self.esc_buf;
        if seq.is_empty() { return; }

        let cmd = seq.as_bytes()[seq.len() - 1] as char;
        let params_str = &seq[..seq.len() - 1];
        let params: Vec<u16> = params_str
            .split(';')
            .filter_map(|s| s.parse().ok())
            .collect();

        let p = |i: usize, default: u16| -> u16 {
            params.get(i).copied().unwrap_or(default)
        };

        match cmd {
            'A' => self.cursor_y = self.cursor_y.saturating_sub(p(0, 1)),
            'B' => self.cursor_y = (self.cursor_y + p(0, 1)).min(self.rows - 1),
            'C' => self.cursor_x = (self.cursor_x + p(0, 1)).min(self.cols - 1),
            'D' => self.cursor_x = self.cursor_x.saturating_sub(p(0, 1)),

            'H' | 'f' => {
                self.cursor_y = p(0, 1).saturating_sub(1).min(self.rows - 1);
                self.cursor_x = p(1, 1).saturating_sub(1).min(self.cols - 1);
            }

            'J' => {
                match p(0, 0) {
                    0 => self.clear_below(),
                    1 => self.clear_above(),
                    2 | 3 => self.clear_all(),
                    _ => {}
                }
            }

            'K' => {
                match p(0, 0) {
                    0 => self.clear_line_right(),
                    1 => self.clear_line_left(),
                    2 => self.clear_line(),
                    _ => {}
                }
            }

            'm' => self.process_sgr(&params),

            'r' => {
                // Scroll region — basit uygulama
            }

            'h' | 'l' => {
                // Mode set/reset
                if params_str.starts_with('?') {
                    let mode = p(0, 0);
                    let enabled = cmd == 'h';
                    match mode {
                        25 => self.cursor_visible = enabled,
                        _ => {}
                    }
                }
            }

            _ => {}
        }
    }

    fn process_sgr(&mut self, params: &[u16]) {
        if params.is_empty() {
            self.current_fg = CellColor::default();
            self.current_bg = CellColor { r: 0.0, g: 0.0, b: 0.0 };
            self.current_style = CellStyle::default();
            return;
        }

        let mut i = 0;
        while i < params.len() {
            match params[i] {
                0 => {
                    self.current_fg = CellColor::default();
                    self.current_bg = CellColor { r: 0.0, g: 0.0, b: 0.0 };
                    self.current_style = CellStyle::default();
                }
                1 => self.current_style.bold = true,
                3 => self.current_style.italic = true,
                4 => self.current_style.underline = true,
                7 => self.current_style.inverse = true,
                9 => self.current_style.strikethrough = true,
                22 => self.current_style.bold = false,
                23 => self.current_style.italic = false,
                24 => self.current_style.underline = false,
                27 => self.current_style.inverse = false,
                29 => self.current_style.strikethrough = false,

                // Ön plan 8 renk
                30..=37 => {
                    let idx = (params[i] - 30) as usize;
                    let palette = crate::config::Config::default().colors.palette;
                    self.current_fg = CellColor {
                        r: palette[idx][0],
                        g: palette[idx][1],
                        b: palette[idx][2],
                    };
                }
                39 => self.current_fg = CellColor::default(),

                // Arka plan 8 renk
                40..=47 => {
                    let idx = (params[i] - 40) as usize;
                    let palette = crate::config::Config::default().colors.palette;
                    self.current_bg = CellColor {
                        r: palette[idx][0],
                        g: palette[idx][1],
                        b: palette[idx][2],
                    };
                }
                49 => self.current_bg = CellColor { r: 0.0, g: 0.0, b: 0.0 },

                // Parlak ön plan
                90..=97 => {
                    let idx = (params[i] - 90 + 8) as usize;
                    let palette = crate::config::Config::default().colors.palette;
                    self.current_fg = CellColor {
                        r: palette[idx][0],
                        g: palette[idx][1],
                        b: palette[idx][2],
                    };
                }

                // Parlak arka plan
                100..=107 => {
                    let idx = (params[i] - 100 + 8) as usize;
                    let palette = crate::config::Config::default().colors.palette;
                    self.current_bg = CellColor {
                        r: palette[idx][0],
                        g: palette[idx][1],
                        b: palette[idx][2],
                    };
                }

                _ => {}
            }
            i += 1;
        }
    }

    // ── Grid İşlemleri ──────────────────────────────────────────

    fn put_char(&mut self, ch: char) {
        let x = self.cursor_x as usize;
        let y = self.cursor_y as usize;

        if y < self.grid.len() && x < self.grid[0].len() {
            self.grid[y][x] = Cell {
                ch,
                fg: self.current_fg,
                bg: self.current_bg,
                style: self.current_style,
            };
        }

        self.cursor_x += 1;
        if self.cursor_x >= self.cols {
            self.cursor_x = 0;
            self.newline();
        }
    }

    fn newline(&mut self) {
        self.cursor_y += 1;
        if self.cursor_y >= self.rows {
            self.scroll_up();
            self.cursor_y = self.rows - 1;
        }
    }

    fn scroll_up(&mut self) {
        if !self.grid.is_empty() {
            let line = self.grid.remove(0);
            if self.scrollback.len() >= self.scrollback_limit {
                self.scrollback.remove(0);
            }
            self.scrollback.push(line);
            self.grid.push(vec![Cell::default(); self.cols as usize]);
        }
    }

    fn clear_all(&mut self) {
        for row in &mut self.grid {
            for cell in row {
                *cell = Cell::default();
            }
        }
    }

    fn clear_below(&mut self) {
        self.clear_line_right();
        for y in (self.cursor_y + 1) as usize..self.rows as usize {
            if y < self.grid.len() {
                for cell in &mut self.grid[y] {
                    *cell = Cell::default();
                }
            }
        }
    }

    fn clear_above(&mut self) {
        self.clear_line_left();
        for y in 0..self.cursor_y as usize {
            if y < self.grid.len() {
                for cell in &mut self.grid[y] {
                    *cell = Cell::default();
                }
            }
        }
    }

    fn clear_line(&mut self) {
        let y = self.cursor_y as usize;
        if y < self.grid.len() {
            for cell in &mut self.grid[y] {
                *cell = Cell::default();
            }
        }
    }

    fn clear_line_right(&mut self) {
        let y = self.cursor_y as usize;
        let x = self.cursor_x as usize;
        if y < self.grid.len() {
            for i in x..self.grid[y].len() {
                self.grid[y][i] = Cell::default();
            }
        }
    }

    fn clear_line_left(&mut self) {
        let y = self.cursor_y as usize;
        let x = self.cursor_x as usize;
        if y < self.grid.len() {
            for i in 0..=x.min(self.grid[y].len() - 1) {
                self.grid[y][i] = Cell::default();
            }
        }
    }
}
