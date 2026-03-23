project(
  'lumiere-compositor',
  'c',
  version: '0.3.0',
  license: 'MIT',
  default_options: [
    'c_std=c11',
    'warning_level=2',
    'werror=false',
  ],
)

# ── Bağımlılıklar ───────────────────────────────────────────────
wayland_server  = dependency('wayland-server')
wayland_protos  = dependency('wayland-protocols', version: '>=1.25')
wlroots         = dependency('wlroots', version: '>=0.17')
xkbcommon       = dependency('xkbcommon')
libinput        = dependency('libinput')
pixman          = dependency('pixman-1')
math            = meson.get_compiler('c').find_library('m')

# ── Wayland protocols scanner ────────────────────────────────────
wl_protocol_dir = wayland_protos.get_variable('pkgdatadir')
wayland_scanner = find_program('wayland-scanner')

protocols = [
  wl_protocol_dir / 'stable/xdg-shell/xdg-shell.xml',
]

protocol_sources = []
protocol_headers = []

foreach proto : protocols
  name = proto.split('/')[-1].split('.')[0]

  protocol_sources += custom_target(
    name + '-protocol',
    input: proto,
    output: name + '-protocol.c',
    command: [wayland_scanner, 'private-code', '@INPUT@', '@OUTPUT@'],
  )

  protocol_headers += custom_target(
    name + '-protocol-header',
    input: proto,
    output: name + '-protocol.h',
    command: [wayland_scanner, 'server-header', '@INPUT@', '@OUTPUT@'],
  )
endforeach

# ── Kaynak dosyalar ──────────────────────────────────────────────
sources = files(
  'src/main.c',
  'src/server.c',
  'src/input.c',
  'src/render.c',
  'src/config.c',
  'src/ipc.c',
)

# ── Derleme ──────────────────────────────────────────────────────
executable(
  'lumiere-compositor',
  sources + protocol_sources + protocol_headers,
  dependencies: [
    wayland_server,
    wlroots,
    xkbcommon,
    libinput,
    pixman,
    math,
  ],
  install: true,
)
