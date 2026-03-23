// ╔══════════════════════════════════════════════════════════════╗
// ║          ✦ Lumière Terminal — PTY Management                 ║
// ╚══════════════════════════════════════════════════════════════╝

use crossbeam_channel::Sender;
use log::{error, info};
use std::ffi::CString;
use std::io::{self, Read, Write};
use std::os::fd::{AsRawFd, FromRawFd, OwnedFd, RawFd};
use std::thread;

/// PTY bağlantısını temsil eder.
pub struct Pty {
    master_fd: OwnedFd,
    child_pid: i32,
}

impl Pty {
    /// Yeni shell spawn et.
    pub fn spawn(
        shell: &str,
        cols: u16,
        rows: u16,
        output_tx: Sender<Vec<u8>>,
    ) -> io::Result<Self> {
        unsafe {
            // PTY aç
            let mut master: RawFd = 0;
            let mut slave: RawFd = 0;

            let mut ws: libc::winsize = std::mem::zeroed();
            ws.ws_col = cols;
            ws.ws_row = rows;
            ws.ws_xpixel = 0;
            ws.ws_ypixel = 0;

            if libc::openpty(&mut master, &mut slave, std::ptr::null_mut(),
                             std::ptr::null_mut(), &ws) != 0 {
                return Err(io::Error::last_os_error());
            }

            let pid = libc::fork();
            if pid < 0 {
                return Err(io::Error::last_os_error());
            }

            if pid == 0 {
                // ── Çocuk İşlem ──
                libc::close(master);
                libc::setsid();

                // Slave'i kontrol terminali yap
                libc::ioctl(slave, libc::TIOCSCTTY, 0);

                // stdin/stdout/stderr → slave
                libc::dup2(slave, 0);
                libc::dup2(slave, 1);
                libc::dup2(slave, 2);

                if slave > 2 {
                    libc::close(slave);
                }

                // Ortam değişkenleri
                let term = CString::new("TERM=xterm-256color").unwrap();
                libc::putenv(term.as_ptr() as *mut _);

                let shell_c = CString::new(shell).unwrap();
                libc::execl(
                    shell_c.as_ptr(),
                    shell_c.as_ptr(),
                    std::ptr::null::<libc::c_char>(),
                );
                libc::_exit(1);
            }

            // ── Ana İşlem ──
            libc::close(slave);

            let master_fd = OwnedFd::from_raw_fd(master);

            // Arka plan okuyucu thread
            let read_fd = master;
            thread::Builder::new()
                .name("pty-reader".into())
                .spawn(move || {
                    let mut file = std::fs::File::from(unsafe {
                        OwnedFd::from_raw_fd(libc::dup(read_fd))
                    });
                    let mut buf = [0u8; 4096];
                    loop {
                        match file.read(&mut buf) {
                            Ok(0) => break,
                            Ok(n) => {
                                if output_tx.send(buf[..n].to_vec()).is_err() {
                                    break;
                                }
                            }
                            Err(e) => {
                                if e.kind() != io::ErrorKind::Interrupted {
                                    error!("PTY okuma hatası: {e}");
                                    break;
                                }
                            }
                        }
                    }
                })
                .expect("PTY reader thread");

            info!("PTY spawn: PID={pid}, shell={shell}");

            Ok(Self {
                master_fd,
                child_pid: pid,
            })
        }
    }

    /// PTY'ye veri yaz (klavye girişi).
    pub fn write(&self, data: &[u8]) {
        use std::os::fd::AsFd;
        let fd = self.master_fd.as_raw_fd();
        unsafe {
            libc::write(fd, data.as_ptr() as *const _, data.len());
        }
    }

    /// Terminal boyutunu güncelle.
    pub fn resize(&self, cols: u16, rows: u16) {
        unsafe {
            let ws = libc::winsize {
                ws_col: cols,
                ws_row: rows,
                ws_xpixel: 0,
                ws_ypixel: 0,
            };
            libc::ioctl(self.master_fd.as_raw_fd(), libc::TIOCSWINSZ, &ws);
        }
    }
}

impl Drop for Pty {
    fn drop(&mut self) {
        unsafe {
            libc::kill(self.child_pid, libc::SIGTERM);
            libc::waitpid(self.child_pid, std::ptr::null_mut(), 0);
        }
    }
}
