#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║          ✦ Lumière OS — Volume / Brightness OSD              ║
# ╚══════════════════════════════════════════════════════════════╝
# Ses ve parlaklık değişikliklerinde mako bildirimi gösterir

NOTIFY_ID=9999

case "$1" in
    volume-up)
        wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+
        VOLUME=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{printf "%.0f", $2 * 100}')
        notify-send -r $NOTIFY_ID -t 1500 -h int:value:$VOLUME "🔊 Ses — ${VOLUME}%"
        ;;
    volume-down)
        wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
        VOLUME=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{printf "%.0f", $2 * 100}')
        notify-send -r $NOTIFY_ID -t 1500 -h int:value:$VOLUME "🔉 Ses — ${VOLUME}%"
        ;;
    volume-mute)
        wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
        MUTED=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -qi 'muted' && echo "Sessiz" || echo "Açık")
        notify-send -r $NOTIFY_ID -t 1500 "🔇 Ses — ${MUTED}"
        ;;
    brightness-up)
        brightnessctl set 5%+
        BRIGHTNESS=$(brightnessctl -m | awk -F, '{print $4}' | tr -d '%')
        notify-send -r $NOTIFY_ID -t 1500 -h int:value:$BRIGHTNESS "☀️ Parlaklık — ${BRIGHTNESS}%"
        ;;
    brightness-down)
        brightnessctl set 5%-
        BRIGHTNESS=$(brightnessctl -m | awk -F, '{print $4}' | tr -d '%')
        notify-send -r $NOTIFY_ID -t 1500 -h int:value:$BRIGHTNESS "🔅 Parlaklık — ${BRIGHTNESS}%"
        ;;
    *)
        echo "Kullanım: lumiere-osd [volume-up|volume-down|volume-mute|brightness-up|brightness-down]"
        exit 1
        ;;
esac
