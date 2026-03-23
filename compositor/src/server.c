/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          ✦ Lumière Compositor — Server Core                  ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * Wayland display, backend, XDG shell ve pencere yönetimi.
 */

#include "server.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* ── XDG Toplevel Callbacks ──────────────────────────────────── */

static void xdg_toplevel_map(struct wl_listener *listener, void *data) {
    struct lumiere_view *view = wl_container_of(listener, view, map);

    /* Aktif workspace'e ekle */
    int ws = view->server->active_workspace;
    view->workspace_id = ws;
    wl_list_insert(&view->server->workspaces[ws].views, &view->workspace_link);

    focus_view(view, view->xdg_toplevel->base->surface);
}

static void xdg_toplevel_unmap(struct wl_listener *listener, void *data) {
    struct lumiere_view *view = wl_container_of(listener, view, unmap);
    wl_list_remove(&view->workspace_link);
}

static void xdg_toplevel_destroy(struct wl_listener *listener, void *data) {
    struct lumiere_view *view = wl_container_of(listener, view, destroy);

    wl_list_remove(&view->map.link);
    wl_list_remove(&view->unmap.link);
    wl_list_remove(&view->destroy.link);
    wl_list_remove(&view->request_move.link);
    wl_list_remove(&view->request_resize.link);
    wl_list_remove(&view->request_maximize.link);
    wl_list_remove(&view->request_fullscreen.link);
    wl_list_remove(&view->link);

    free(view);
}

static void xdg_toplevel_request_move(struct wl_listener *listener, void *data) {
    struct lumiere_view *view = wl_container_of(listener, view, request_move);
    struct lumiere_server *server = view->server;

    /* Sadece floating pencereler taşınabilir */
    if (!view->floating) return;

    server->grabbed_view = view;
    server->cursor_mode = LUMIERE_CURSOR_MOVE;

    server->grab_x = server->cursor->x - view->x;
    server->grab_y = server->cursor->y - view->y;
}

static void xdg_toplevel_request_resize(struct wl_listener *listener, void *data) {
    struct lumiere_view *view = wl_container_of(listener, view, request_resize);
    struct wlr_xdg_toplevel_resize_event *event = data;
    struct lumiere_server *server = view->server;

    if (!view->floating) return;

    server->grabbed_view = view;
    server->cursor_mode = LUMIERE_CURSOR_RESIZE;
    server->resize_edges = event->edges;

    struct wlr_box geo;
    wlr_xdg_surface_get_geometry(view->xdg_toplevel->base, &geo);

    server->grab_x = server->cursor->x;
    server->grab_y = server->cursor->y;
    server->grab_geobox.x = view->x;
    server->grab_geobox.y = view->y;
    server->grab_geobox.width = geo.width;
    server->grab_geobox.height = geo.height;
}

static void xdg_toplevel_request_maximize(struct wl_listener *listener, void *data) {
    struct lumiere_view *view = wl_container_of(listener, view, request_maximize);
    if (view->xdg_toplevel->base->initialized) {
        wlr_xdg_surface_schedule_configure(view->xdg_toplevel->base);
    }
}

static void xdg_toplevel_request_fullscreen(struct wl_listener *listener, void *data) {
    struct lumiere_view *view = wl_container_of(listener, view, request_fullscreen);
    view->fullscreen = !view->fullscreen;
    wlr_xdg_toplevel_set_fullscreen(view->xdg_toplevel, view->fullscreen);
}

/* ── Yeni XDG Toplevel ───────────────────────────────────────── */
static void server_new_xdg_toplevel(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, new_xdg_toplevel);
    struct wlr_xdg_toplevel *toplevel = data;

    /* Yeni view oluştur */
    struct lumiere_view *view = calloc(1, sizeof(*view));
    view->server = server;
    view->xdg_toplevel = toplevel;
    view->floating = false;
    view->fullscreen = false;
    view->anim_progress = 0.0f;
    view->anim_active = server->config.animations_enabled;

    /* Scene tree */
    view->scene_tree = wlr_scene_xdg_surface_create(
        &server->scene->tree, toplevel->base);
    view->scene_tree->node.data = view;
    toplevel->base->data = view->scene_tree;

    /* Listeners bağla */
    view->map.notify = xdg_toplevel_map;
    wl_signal_add(&toplevel->base->surface->events.map, &view->map);

    view->unmap.notify = xdg_toplevel_unmap;
    wl_signal_add(&toplevel->base->surface->events.unmap, &view->unmap);

    view->destroy.notify = xdg_toplevel_destroy;
    wl_signal_add(&toplevel->events.destroy, &view->destroy);

    view->request_move.notify = xdg_toplevel_request_move;
    wl_signal_add(&toplevel->events.request_move, &view->request_move);

    view->request_resize.notify = xdg_toplevel_request_resize;
    wl_signal_add(&toplevel->events.request_resize, &view->request_resize);

    view->request_maximize.notify = xdg_toplevel_request_maximize;
    wl_signal_add(&toplevel->events.request_maximize, &view->request_maximize);

    view->request_fullscreen.notify = xdg_toplevel_request_fullscreen;
    wl_signal_add(&toplevel->events.request_fullscreen, &view->request_fullscreen);

    wl_list_insert(&server->views, &view->link);
}

/* ── XDG Popup ───────────────────────────────────────────────── */
static void server_new_xdg_popup(struct wl_listener *listener, void *data) {
    struct wlr_xdg_popup *popup = data;

    struct wlr_xdg_surface *parent =
        wlr_xdg_surface_try_from_wlr_surface(popup->parent);
    assert(parent != NULL);

    struct wlr_scene_tree *parent_tree = parent->data;
    wlr_scene_xdg_surface_create(parent_tree, popup->base);
}

/* ── View Helpers ────────────────────────────────────────────── */

struct lumiere_view *desktop_view_at(
    struct lumiere_server *server, double lx, double ly,
    struct wlr_surface **surface, double *sx, double *sy)
{
    struct wlr_scene_node *node =
        wlr_scene_node_at(&server->scene->tree.node, lx, ly, sx, sy);

    if (node == NULL || node->type != WLR_SCENE_NODE_BUFFER) {
        return NULL;
    }

    struct wlr_scene_buffer *scene_buffer = wlr_scene_buffer_from_node(node);
    struct wlr_scene_surface *scene_surface =
        wlr_scene_surface_try_from_buffer(scene_buffer);

    if (!scene_surface) {
        return NULL;
    }

    *surface = scene_surface->surface;

    /* Scene tree'den view'a ulaş */
    struct wlr_scene_tree *tree = node->parent;
    while (tree != NULL && tree->node.data == NULL) {
        tree = tree->node.parent;
    }

    return tree ? tree->node.data : NULL;
}

void focus_view(struct lumiere_view *view, struct wlr_surface *surface) {
    if (view == NULL) return;

    struct lumiere_server *server = view->server;
    struct wlr_seat *seat = server->seat;
    struct wlr_surface *prev_surface = seat->keyboard_state.focused_surface;

    if (prev_surface == surface) return;

    /* Önceki odağı kaldır */
    if (prev_surface) {
        struct wlr_xdg_toplevel *prev_toplevel =
            wlr_xdg_toplevel_try_from_wlr_surface(prev_surface);
        if (prev_toplevel) {
            wlr_xdg_toplevel_set_activated(prev_toplevel, false);
        }
    }

    /* Scene node'u üste taşı */
    wlr_scene_node_raise_to_top(&view->scene_tree->node);

    /* Views listesinde en başa al */
    wl_list_remove(&view->link);
    wl_list_insert(&server->views, &view->link);

    /* Aktive et */
    wlr_xdg_toplevel_set_activated(view->xdg_toplevel, true);

    /* Klavye odağını ayarla */
    struct wlr_keyboard *keyboard = wlr_seat_get_keyboard(seat);
    if (keyboard) {
        wlr_seat_keyboard_notify_enter(seat, view->xdg_toplevel->base->surface,
            keyboard->keycodes, keyboard->num_keycodes, &keyboard->modifiers);
    }
}

/* ── Server Init / Destroy / Run ─────────────────────────────── */

bool server_init(struct lumiere_server *server) {
    /* Wayland display */
    server->wl_display = wl_display_create();
    if (!server->wl_display) {
        wlr_log(WLR_ERROR, "wl_display oluşturulamadı");
        return false;
    }

    server->wl_event_loop = wl_display_get_event_loop(server->wl_display);

    /* Backend */
    server->backend = wlr_backend_autocreate(
        server->wl_event_loop, NULL);
    if (!server->backend) {
        wlr_log(WLR_ERROR, "wlr_backend oluşturulamadı");
        return false;
    }

    /* Renderer */
    server->renderer = wlr_renderer_autocreate(server->backend);
    if (!server->renderer) {
        wlr_log(WLR_ERROR, "Renderer oluşturulamadı");
        return false;
    }
    wlr_renderer_init_wl_display(server->renderer, server->wl_display);

    /* Allocator */
    server->allocator = wlr_allocator_autocreate(
        server->backend, server->renderer);
    if (!server->allocator) {
        wlr_log(WLR_ERROR, "Allocator oluşturulamadı");
        return false;
    }

    /* Compositor & Subcompositor */
    wlr_compositor_create(server->wl_display, 5, server->renderer);
    wlr_subcompositor_create(server->wl_display);

    /* Data device manager */
    wlr_data_device_manager_create(server->wl_display);

    /* Output layout */
    server->output_layout = wlr_output_layout_create(server->wl_display);
    wl_list_init(&server->outputs);

    server->new_output.notify = server_new_output;
    wl_signal_add(&server->backend->events.new_output, &server->new_output);

    /* Scene graph */
    server->scene = wlr_scene_create();
    server->scene_layout = wlr_scene_attach_output_layout(
        server->scene, server->output_layout);

    /* XDG Shell */
    server->xdg_shell = wlr_xdg_shell_create(server->wl_display, 3);
    wl_list_init(&server->views);

    server->new_xdg_toplevel.notify = server_new_xdg_toplevel;
    wl_signal_add(&server->xdg_shell->events.new_toplevel,
                  &server->new_xdg_toplevel);

    server->new_xdg_popup.notify = server_new_xdg_popup;
    wl_signal_add(&server->xdg_shell->events.new_popup,
                  &server->new_xdg_popup);

    /* Cursor */
    server->cursor = wlr_cursor_create();
    wlr_cursor_attach_output_layout(server->cursor, server->output_layout);

    server->cursor_mgr = wlr_xcursor_manager_create("Lumiere-Cursors",
        server->config.cursor_size);

    server->cursor_motion.notify = cursor_motion;
    wl_signal_add(&server->cursor->events.motion, &server->cursor_motion);

    server->cursor_motion_absolute.notify = cursor_motion_absolute;
    wl_signal_add(&server->cursor->events.motion_absolute,
                  &server->cursor_motion_absolute);

    server->cursor_button.notify = cursor_button;
    wl_signal_add(&server->cursor->events.button, &server->cursor_button);

    server->cursor_axis.notify = cursor_axis;
    wl_signal_add(&server->cursor->events.axis, &server->cursor_axis);

    server->cursor_frame.notify = cursor_frame;
    wl_signal_add(&server->cursor->events.frame, &server->cursor_frame);

    /* Seat */
    server->seat = wlr_seat_create(server->wl_display, "seat0");
    wl_list_init(&server->keyboards);

    server->new_input.notify = server_new_input;
    wl_signal_add(&server->backend->events.new_input, &server->new_input);

    server->request_set_cursor.notify = seat_request_cursor;
    wl_signal_add(&server->seat->events.request_set_cursor,
                  &server->request_set_cursor);

    server->request_set_selection.notify = seat_request_set_selection;
    wl_signal_add(&server->seat->events.request_set_selection,
                  &server->request_set_selection);

    /* Workspaces */
    for (int i = 0; i < 10; i++) {
        server->workspaces[i].id = i;
        wl_list_init(&server->workspaces[i].views);
    }
    server->active_workspace = 0;

    /* Keybindings */
    wl_list_init(&server->keybinds);

    /* Wayland socket */
    const char *socket = wl_display_add_socket_auto(server->wl_display);
    if (!socket) {
        wlr_log(WLR_ERROR, "Wayland socket oluşturulamadı");
        return false;
    }

    /* Backend başlat */
    if (!wlr_backend_start(server->backend)) {
        wlr_log(WLR_ERROR, "Backend başlatılamadı");
        return false;
    }

    setenv("WAYLAND_DISPLAY", socket, true);
    wlr_log(WLR_INFO, "✦ Lumière Compositor — WAYLAND_DISPLAY=%s", socket);

    return true;
}

void server_run(struct lumiere_server *server) {
    wl_display_run(server->wl_display);
}

void server_destroy(struct lumiere_server *server) {
    wl_display_destroy_clients(server->wl_display);
    wlr_scene_node_destroy(&server->scene->tree.node);
    wlr_xcursor_manager_destroy(server->cursor_mgr);
    wlr_cursor_destroy(server->cursor);
    wlr_allocator_destroy(server->allocator);
    wlr_renderer_destroy(server->renderer);
    wlr_backend_destroy(server->backend);
    wl_display_destroy(server->wl_display);
}
