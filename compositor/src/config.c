/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          ✦ Lumière Compositor — Configuration               ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * Konfigürasyon dosyası okuma ve varsayılan ayarlar.
 */

#include "server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* ── Varsayılan Ayarlar ──────────────────────────────────────── */
void config_load_defaults(struct lumiere_config *config) {
    config->gaps_inner = 4;
    config->gaps_outer = 8;
    config->border_width = 2;
    config->border_radius = 8;

    /* Lumière Gold — aktif border */
    config->border_color_active[0] = LUMIERE_GOLD_R;
    config->border_color_active[1] = LUMIERE_GOLD_G;
    config->border_color_active[2] = LUMIERE_GOLD_B;
    config->border_color_active[3] = 0.93f;

    /* Koyu border — pasif */
    config->border_color_inactive[0] = LUMIERE_BORDER_R;
    config->border_color_inactive[1] = LUMIERE_BORDER_G;
    config->border_color_inactive[2] = LUMIERE_BORDER_B;
    config->border_color_inactive[3] = 0.53f;

    /* Arkaplan */
    config->bg_color[0] = LUMIERE_BG_BASE_R;
    config->bg_color[1] = LUMIERE_BG_BASE_G;
    config->bg_color[2] = LUMIERE_BG_BASE_B;
    config->bg_color[3] = 1.0f;

    config->animations_enabled = true;
    config->animation_duration_ms = 250;

    strncpy(config->kb_layout, "tr", sizeof(config->kb_layout) - 1);
    config->kb_variant[0] = '\0';

    config->cursor_size = 24;
    config->natural_scroll = true;
    config->tap_to_click = true;
    config->workspace_count = 9;

    snprintf(config->ipc_socket_path, sizeof(config->ipc_socket_path),
             "/tmp/lumiere-compositor.%d.sock", getpid());
}

/* ── INI-benzeri Parser ──────────────────────────────────────── */

static char *trim(char *str) {
    while (isspace((unsigned char)*str)) str++;
    if (*str == '\0') return str;

    char *end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) end--;
    end[1] = '\0';
    return str;
}

static void parse_color(const char *value, float color[4]) {
    /* #RRGGBB veya #RRGGBBAA formatı */
    if (value[0] == '#') value++;
    unsigned int r, g, b, a = 255;
    int n = sscanf(value, "%2x%2x%2x%2x", &r, &g, &b, &a);
    if (n >= 3) {
        color[0] = r / 255.0f;
        color[1] = g / 255.0f;
        color[2] = b / 255.0f;
        color[3] = a / 255.0f;
    }
}

bool config_load_file(struct lumiere_config *config, const char *path) {
    FILE *file = fopen(path, "r");
    if (!file) return false;

    wlr_log(WLR_INFO, "Konfigürasyon yükleniyor: %s", path);

    char line[512];
    char section[64] = "";

    while (fgets(line, sizeof(line), file)) {
        char *trimmed = trim(line);

        /* Boş satır veya yorum */
        if (trimmed[0] == '\0' || trimmed[0] == '#' || trimmed[0] == ';')
            continue;

        /* Bölüm başlığı [section] */
        if (trimmed[0] == '[') {
            char *end = strchr(trimmed, ']');
            if (end) {
                *end = '\0';
                strncpy(section, trimmed + 1, sizeof(section) - 1);
            }
            continue;
        }

        /* key = value */
        char *eq = strchr(trimmed, '=');
        if (!eq) continue;

        *eq = '\0';
        char *key = trim(trimmed);
        char *value = trim(eq + 1);

        /* ── General ─── */
        if (strcmp(section, "general") == 0) {
            if (strcmp(key, "gaps_inner") == 0)
                config->gaps_inner = atoi(value);
            else if (strcmp(key, "gaps_outer") == 0)
                config->gaps_outer = atoi(value);
            else if (strcmp(key, "border_width") == 0)
                config->border_width = atoi(value);
            else if (strcmp(key, "border_radius") == 0)
                config->border_radius = atoi(value);
        }
        /* ── Colors ─── */
        else if (strcmp(section, "colors") == 0) {
            if (strcmp(key, "border_active") == 0)
                parse_color(value, config->border_color_active);
            else if (strcmp(key, "border_inactive") == 0)
                parse_color(value, config->border_color_inactive);
            else if (strcmp(key, "background") == 0)
                parse_color(value, config->bg_color);
        }
        /* ── Animations ─── */
        else if (strcmp(section, "animations") == 0) {
            if (strcmp(key, "enabled") == 0)
                config->animations_enabled = (strcmp(value, "true") == 0);
            else if (strcmp(key, "duration") == 0)
                config->animation_duration_ms = atoi(value);
        }
        /* ── Input ─── */
        else if (strcmp(section, "input") == 0) {
            if (strcmp(key, "kb_layout") == 0)
                strncpy(config->kb_layout, value, sizeof(config->kb_layout) - 1);
            else if (strcmp(key, "kb_variant") == 0)
                strncpy(config->kb_variant, value, sizeof(config->kb_variant) - 1);
            else if (strcmp(key, "cursor_size") == 0)
                config->cursor_size = atoi(value);
            else if (strcmp(key, "natural_scroll") == 0)
                config->natural_scroll = (strcmp(value, "true") == 0);
            else if (strcmp(key, "tap_to_click") == 0)
                config->tap_to_click = (strcmp(value, "true") == 0);
        }
    }

    fclose(file);
    return true;
}
