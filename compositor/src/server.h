/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          ✦ Lumière Compositor — Server Header                ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * Ana veri yapıları ve fonksiyon tanımları.
 */

#ifndef LUMIERE_SERVER_H
#define LUMIERE_SERVER_H

#include <wayland-server-core.h>
#include <wlr/backend.h>
#include <wlr/render/allocator.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/types/wlr_compositor.h>
#include <wlr/types/wlr_cursor.h>
#include <wlr/types/wlr_data_device.h>
#include <wlr/types/wlr_input_device.h>
#include <wlr/types/wlr_keyboard.h>
#include <wlr/types/wlr_output.h>
#include <wlr/types/wlr_output_layout.h>
#include <wlr/types/wlr_pointer.h>
#include <wlr/types/wlr_scene.h>
#include <wlr/types/wlr_seat.h>
#include <wlr/types/wlr_subcompositor.h>
#include <wlr/types/wlr_xcursor_manager.h>
#include <wlr/types/wlr_xdg_shell.h>
#include <wlr/util/log.h>
#include <xkbcommon/xkbcommon.h>
#include <stdbool.h>

/* ── Lumière Renk Paleti ─────────────────────────────────────── */
#define LUMIERE_GOLD_R         0.961f
#define LUMIERE_GOLD_G         0.651f
#define LUMIERE_GOLD_B         0.137f
#define LUMIERE_GOLD_LIGHT_R   1.000f
#define LUMIERE_GOLD_LIGHT_G   0.816f
#define LUMIERE_GOLD_LIGHT_B   0.502f
#define LUMIERE_BG_BASE_R      0.051f
#define LUMIERE_BG_BASE_G      0.051f
#define LUMIERE_BG_BASE_B      0.078f
#define LUMIERE_BORDER_R       0.165f
#define LUMIERE_BORDER_G       0.165f
#define LUMIERE_BORDER_B       0.259f

/* ── Cursor Modları ──────────────────────────────────────────── */
enum lumiere_cursor_mode {
    LUMIERE_CURSOR_PASSTHROUGH,
    LUMIERE_CURSOR_MOVE,
    LUMIERE_CURSOR_RESIZE,
};

/* ── Konfigürasyon ───────────────────────────────────────────── */
struct lumiere_config {
    int gaps_inner;
    int gaps_outer;
    int border_width;
    int border_radius;
    float border_color_active[4];
    float border_color_inactive[4];
    float bg_color[4];
    bool animations_enabled;
    int animation_duration_ms;
    char kb_layout[32];
    char kb_variant[32];
    int cursor_size;
    bool natural_scroll;
    bool tap_to_click;
    int workspace_count;
    char ipc_socket_path[256];
};

/* ── Keybinding ──────────────────────────────────────────────── */
struct lumiere_keybind {
    uint32_t modifiers;
    xkb_keysym_t keysym;
    char command[256];
    struct wl_list link;
};

/* ── Workspace ───────────────────────────────────────────────── */
struct lumiere_workspace {
    int id;
    struct wl_list views;  /* lumiere_view::workspace_link */
    struct wlr_scene_tree *scene_tree;
};

/* ── View (Pencere) ──────────────────────────────────────────── */
struct lumiere_view {
    struct wl_list link;            /* server::views */
    struct wl_list workspace_link;  /* workspace::views */
    struct lumiere_server *server;
    struct wlr_xdg_toplevel *xdg_toplevel;
    struct wlr_scene_tree *scene_tree;

    /* Pozisyon ve boyut */
    int x, y;
    int width, height;
    bool floating;
    bool fullscreen;
    int workspace_id;

    /* Animasyon */
    float anim_progress;  /* 0.0 - 1.0 */
    bool anim_active;

    /* Listeners */
    struct wl_listener map;
    struct wl_listener unmap;
    struct wl_listener destroy;
    struct wl_listener request_move;
    struct wl_listener request_resize;
    struct wl_listener request_maximize;
    struct wl_listener request_fullscreen;
};

/* ── Output (Monitör) ────────────────────────────────────────── */
struct lumiere_output {
    struct wl_list link;
    struct lumiere_server *server;
    struct wlr_output *wlr_output;
    struct wl_listener frame;
    struct wl_listener request_state;
    struct wl_listener destroy;
};

/* ── Keyboard ────────────────────────────────────────────────── */
struct lumiere_keyboard {
    struct wl_list link;
    struct lumiere_server *server;
    struct wlr_keyboard *wlr_keyboard;
    struct wl_listener modifiers;
    struct wl_listener key;
    struct wl_listener destroy;
};

/* ── Ana Server ──────────────────────────────────────────────── */
struct lumiere_server {
    struct wl_display *wl_display;
    struct wl_event_loop *wl_event_loop;
    struct wlr_backend *backend;
    struct wlr_renderer *renderer;
    struct wlr_allocator *allocator;
    struct wlr_scene *scene;
    struct wlr_scene_output_layout *scene_layout;

    /* Shell */
    struct wlr_xdg_shell *xdg_shell;
    struct wl_listener new_xdg_toplevel;
    struct wl_listener new_xdg_popup;
    struct wl_list views;

    /* Output */
    struct wlr_output_layout *output_layout;
    struct wl_list outputs;
    struct wl_listener new_output;

    /* Input */
    struct wlr_cursor *cursor;
    struct wlr_xcursor_manager *cursor_mgr;
    struct wl_listener cursor_motion;
    struct wl_listener cursor_motion_absolute;
    struct wl_listener cursor_button;
    struct wl_listener cursor_axis;
    struct wl_listener cursor_frame;

    struct wlr_seat *seat;
    struct wl_listener new_input;
    struct wl_listener request_set_cursor;
    struct wl_listener request_set_selection;
    struct wl_list keyboards;

    /* Cursor interaction */
    enum lumiere_cursor_mode cursor_mode;
    struct lumiere_view *grabbed_view;
    double grab_x, grab_y;
    struct wlr_box grab_geobox;
    uint32_t resize_edges;

    /* Workspaces */
    struct lumiere_workspace workspaces[10];
    int active_workspace;

    /* Config */
    struct lumiere_config config;

    /* Keybindings */
    struct wl_list keybinds;

    /* IPC */
    int ipc_socket_fd;
    struct wl_event_source *ipc_event_source;
};

/* ── Fonksiyon Tanımları ─────────────────────────────────────── */

/* server.c */
bool server_init(struct lumiere_server *server);
void server_destroy(struct lumiere_server *server);
void server_run(struct lumiere_server *server);
struct lumiere_view *desktop_view_at(
    struct lumiere_server *server, double lx, double ly,
    struct wlr_surface **surface, double *sx, double *sy);
void focus_view(struct lumiere_view *view, struct wlr_surface *surface);

/* input.c */
void server_new_input(struct wl_listener *listener, void *data);
void seat_request_cursor(struct wl_listener *listener, void *data);
void seat_request_set_selection(struct wl_listener *listener, void *data);
void cursor_motion(struct wl_listener *listener, void *data);
void cursor_motion_absolute(struct wl_listener *listener, void *data);
void cursor_button(struct wl_listener *listener, void *data);
void cursor_axis(struct wl_listener *listener, void *data);
void cursor_frame(struct wl_listener *listener, void *data);

/* render.c */
void output_frame(struct wl_listener *listener, void *data);
void output_request_state(struct wl_listener *listener, void *data);
void output_destroy(struct wl_listener *listener, void *data);
void server_new_output(struct wl_listener *listener, void *data);

/* config.c */
void config_load_defaults(struct lumiere_config *config);
bool config_load_file(struct lumiere_config *config, const char *path);

/* ipc.c */
bool ipc_init(struct lumiere_server *server);
void ipc_destroy(struct lumiere_server *server);

#endif /* LUMIERE_SERVER_H */
