# shellcheck disable=SC2148,SC2296,SC1090,SC2016,SC1071
# ╔══════════════════════════════════════════════════════════════╗
# ║              ✦ Lumière OS — Zsh Konfigürasyonu               ║
# ╚══════════════════════════════════════════════════════════════╝

# ─── Zinit (Plugin Manager) ─────────────────────────────────────
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"

if [[ ! -d "$ZINIT_HOME" ]]; then
    mkdir -p "$(dirname $ZINIT_HOME)"
    git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi

source "${ZINIT_HOME}/zinit.zsh"

# ─── Eklentiler ─────────────────────────────────────────────────
# Syntax highlighting
zinit light zsh-users/zsh-syntax-highlighting

# Otomatik tamamlama önerileri
zinit light zsh-users/zsh-autosuggestions

# Daha iyi tamamlama
zinit light zsh-users/zsh-completions

# fzf-tab — tab completion with fzf
zinit light Aloxaf/fzf-tab

# ─── Geçmiş ────────────────────────────────────────────────────
HISTSIZE=10000
SAVEHIST=10000
HISTFILE=~/.zsh_history
HISTDUP=erase

setopt appendhistory
setopt sharehistory
setopt hist_ignore_space
setopt hist_ignore_all_dups
setopt hist_save_no_dups
setopt hist_ignore_dups
setopt hist_find_no_dups

# ─── Tamamlama Ayarları ────────────────────────────────────────
autoload -Uz compinit && compinit
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' menu no
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'ls --color $realpath'
zstyle ':fzf-tab:complete:__zoxide_z:*' fzf-preview 'ls --color $realpath'

# ─── Anahtar Bağlamaları ───────────────────────────────────────
bindkey -e
bindkey '^p' history-search-backward
bindkey '^n' history-search-forward
bindkey '^[[A' history-search-backward
bindkey '^[[B' history-search-forward

# ─── Alias'lar ──────────────────────────────────────────────────
# Temel
alias ls='ls --color=auto'
alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias df='df -h'
alias du='du -h'
alias free='free -h'
alias clear='clear && fastfetch'

# Lumière paket yönetimi
alias linstall='lumiere-pkg install'
alias lremove='lumiere-pkg remove'
alias lupdate='lumiere-pkg update'
alias lsearch='lumiere-pkg search'

# Git kısayolları
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline -20'
alias gd='git diff'

# Güvenlik
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# ─── Ortam Değişkenleri ────────────────────────────────────────
export EDITOR="nano"
export VISUAL="nano"
export TERMINAL="kitty"
export BROWSER="firefox"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_STATE_HOME="$HOME/.local/state"

# ─── PATH ───────────────────────────────────────────────────────
export PATH="$HOME/.local/bin:$PATH"

# ─── Araç Entegrasyonları ──────────────────────────────────────
# fzf entegrasyonu
[ -f /usr/share/fzf/key-bindings.zsh ] && source /usr/share/fzf/key-bindings.zsh
[ -f /usr/share/fzf/completion.zsh ] && source /usr/share/fzf/completion.zsh

export FZF_DEFAULT_OPTS="
  --color=bg+:#1A1A2E,bg:#0D0D14,spinner:#F5A623,hl:#F5A623
  --color=fg:#E8E6F0,header:#F5A623,info:#C084FC,pointer:#F5A623
  --color=marker:#4ADE80,fg+:#E8E6F0,prompt:#F5A623,hl+:#FFD080
  --border='rounded' --border-label='' --preview-window='border-rounded'
  --prompt='❯ ' --marker='✦' --pointer='▸'
"

# zoxide (smarter cd)
eval "$(zoxide init zsh)"

# Starship prompt
eval "$(starship init zsh)"
