# ╔══════════════════════════════════════════════════════════════╗
# ║              ✦ Lumière OS — Zsh Environment                  ║
# ╚══════════════════════════════════════════════════════════════╝

# XDG Base Directories
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_STATE_HOME="$HOME/.local/state"

# Varsayılan uygulamalar
export EDITOR="nano"
export VISUAL="nano"
export TERMINAL="kitty"
export BROWSER="firefox"

# Wayland
export MOZ_ENABLE_WAYLAND=1
export QT_QPA_PLATFORM="wayland;xcb"
export GDK_BACKEND="wayland,x11"
export SDL_VIDEODRIVER="wayland"
export CLUTTER_BACKEND="wayland"
export _JAVA_AWT_WM_NONREPARENTING=1
