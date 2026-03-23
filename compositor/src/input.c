/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          ✦ Lumière Compositor — Input Handling               ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * Klavye, fare ve touchpad giriş yönetimi.
 */

#include "server.h"
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* ── Klavye: Tuş Basma ───────────────────────────────────────── */

static bool handle_keybinding(struct lumiere_server *server,
                              xkb_keysym_t sym, uint32_t modifiers) {
    /* Kullanıcı tanımlı keybinding'leri kontrol et */
    struct lumiere_keybind *bind;
    wl_list_for_each(bind, &server->keybinds, link) {
        if (bind->keysym == sym && bind->modifiers == modifiers) {
            if (fork() == 0) {
                execl("/bin/sh", "/bin/sh", "-c", bind->command, NULL);
                _exit(1);
            }
            return true;
        }
    }

    /* Dahili kısayollar (SUPER + key) */
    if (!(modifiers & WLR_MODIFIER_LOGO)) return false;

    switch (sym) {
    case XKB_KEY_Escape:
        /* Super+Escape: Compositor'dan çık */
        wl_display_terminate(server->wl_display);
        return true;

    case XKB_KEY_Return:
        /* Super+Return: Terminal aç */
        if (fork() == 0) {
            execl("/bin/sh", "/bin/sh", "-c", "kitty", NULL);
            _exit(1);
        }
        return true;

    case XKB_KEY_q:
    case XKB_KEY_Q:
        /* Super+Q: Aktif pencereyi kapat */
        if (!wl_list_empty(&server->views)) {
            struct lumiere_view *view = wl_container_of(
                server->views.next, view, link);
            wlr_xdg_toplevel_send_close(view->xdg_toplevel);
        }
        return true;

    case XKB_KEY_v:
    case XKB_KEY_V:
        /* Super+V: Float toggle */
        if (!wl_list_empty(&server->views)) {
            struct lumiere_view *view = wl_container_of(
                server->views.next, view, link);
            view->floating = !view->floating;
        }
        return true;

    case XKB_KEY_f:
    case XKB_KEY_F:
        /* Super+F: Fullscreen toggle */
        if (!wl_list_empty(&server->views)) {
            struct lumiere_view *view = wl_container_of(
                server->views.next, view, link);
            view->fullscreen = !view->fullscreen;
            wlr_xdg_toplevel_set_fullscreen(view->xdg_toplevel,
                                            view->fullscreen);
        }
        return true;

    case XKB_KEY_1: case XKB_KEY_2: case XKB_KEY_3:
    case XKB_KEY_4: case XKB_KEY_5: case XKB_KEY_6:
    case XKB_KEY_7: case XKB_KEY_8: case XKB_KEY_9:
        /* Super+1-9: Workspace geçişi */
        {
            int ws = sym - XKB_KEY_1;
            if (ws >= 0 && ws < 10) {
                server->active_workspace = ws;
                /* TODO: workspace visibility güncelle */
            }
        }
        return true;

    default:
        return false;
    }
}

static void keyboard_key(struct wl_listener *listener, void *data) {
    struct lumiere_keyboard *keyboard =
        wl_container_of(listener, keyboard, key);
    struct lumiere_server *server = keyboard->server;
    struct wlr_keyboard_key_event *event = data;

    uint32_t keycode = event->keycode + 8;
    const xkb_keysym_t *syms;
    int nsyms = xkb_state_key_get_syms(
        keyboard->wlr_keyboard->xkb_state, keycode, &syms);

    bool handled = false;
    uint32_t modifiers = wlr_keyboard_get_modifiers(keyboard->wlr_keyboard);

    if (event->state == WL_KEYBOARD_KEY_STATE_PRESSED) {
        for (int i = 0; i < nsyms; i++) {
            handled = handle_keybinding(server, syms[i], modifiers);
            if (handled) break;
        }
    }

    if (!handled) {
        wlr_seat_set_keyboard(server->seat, keyboard->wlr_keyboard);
        wlr_seat_keyboard_notify_key(server->seat, event->time_msec,
                                     event->keycode, event->state);
    }
}

static void keyboard_modifiers(struct wl_listener *listener, void *data) {
    struct lumiere_keyboard *keyboard =
        wl_container_of(listener, keyboard, modifiers);

    wlr_seat_set_keyboard(keyboard->server->seat, keyboard->wlr_keyboard);
    wlr_seat_keyboard_notify_modifiers(keyboard->server->seat,
        &keyboard->wlr_keyboard->modifiers);
}

static void keyboard_destroy(struct wl_listener *listener, void *data) {
    struct lumiere_keyboard *keyboard =
        wl_container_of(listener, keyboard, destroy);

    wl_list_remove(&keyboard->modifiers.link);
    wl_list_remove(&keyboard->key.link);
    wl_list_remove(&keyboard->destroy.link);
    wl_list_remove(&keyboard->link);
    free(keyboard);
}

/* ── Yeni Input Device ───────────────────────────────────────── */

static void server_new_keyboard(struct lumiere_server *server,
                                struct wlr_input_device *device) {
    struct wlr_keyboard *wlr_keyboard = wlr_keyboard_from_input_device(device);

    struct lumiere_keyboard *keyboard = calloc(1, sizeof(*keyboard));
    keyboard->server = server;
    keyboard->wlr_keyboard = wlr_keyboard;

    /* XKB konfigürasyonu */
    struct xkb_context *context = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
    struct xkb_rule_names rules = {
        .layout = server->config.kb_layout,
        .variant = server->config.kb_variant,
    };
    struct xkb_keymap *keymap = xkb_keymap_new_from_names(
        context, &rules, XKB_KEYMAP_COMPILE_NO_FLAGS);

    wlr_keyboard_set_keymap(wlr_keyboard, keymap);
    xkb_keymap_unref(keymap);
    xkb_context_unref(context);

    wlr_keyboard_set_repeat_info(wlr_keyboard, 25, 600);

    /* Listeners */
    keyboard->modifiers.notify = keyboard_modifiers;
    wl_signal_add(&wlr_keyboard->events.modifiers, &keyboard->modifiers);

    keyboard->key.notify = keyboard_key;
    wl_signal_add(&wlr_keyboard->events.key, &keyboard->key);

    keyboard->destroy.notify = keyboard_destroy;
    wl_signal_add(&device->events.destroy, &keyboard->destroy);

    wlr_seat_set_keyboard(server->seat, wlr_keyboard);
    wl_list_insert(&server->keyboards, &keyboard->link);
}

static void server_new_pointer(struct lumiere_server *server,
                               struct wlr_input_device *device) {
    wlr_cursor_attach_input_device(server->cursor, device);
}

void server_new_input(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, new_input);
    struct wlr_input_device *device = data;

    switch (device->type) {
    case WLR_INPUT_DEVICE_KEYBOARD:
        server_new_keyboard(server, device);
        break;
    case WLR_INPUT_DEVICE_POINTER:
    case WLR_INPUT_DEVICE_TOUCH:
    case WLR_INPUT_DEVICE_TABLET:
        server_new_pointer(server, device);
        break;
    default:
        break;
    }

    /* Seat capabilities güncelle */
    uint32_t caps = WL_SEAT_CAPABILITY_POINTER;
    if (!wl_list_empty(&server->keyboards)) {
        caps |= WL_SEAT_CAPABILITY_KEYBOARD;
    }
    wlr_seat_set_capabilities(server->seat, caps);
}

/* ── Cursor Callbacks ────────────────────────────────────────── */

static void process_cursor_move(struct lumiere_server *server, uint32_t time) {
    struct lumiere_view *view = server->grabbed_view;
    view->x = server->cursor->x - server->grab_x;
    view->y = server->cursor->y - server->grab_y;
    wlr_scene_node_set_position(&view->scene_tree->node, view->x, view->y);
}

static void process_cursor_resize(struct lumiere_server *server, uint32_t time) {
    struct lumiere_view *view = server->grabbed_view;
    double dx = server->cursor->x - server->grab_x;
    double dy = server->cursor->y - server->grab_y;

    double x = server->grab_geobox.x;
    double y = server->grab_geobox.y;
    int width = server->grab_geobox.width;
    int height = server->grab_geobox.height;

    if (server->resize_edges & WLR_EDGE_RIGHT) {
        width += dx;
    } else if (server->resize_edges & WLR_EDGE_LEFT) {
        width -= dx;
        x += dx;
    }

    if (server->resize_edges & WLR_EDGE_BOTTOM) {
        height += dy;
    } else if (server->resize_edges & WLR_EDGE_TOP) {
        height -= dy;
        y += dy;
    }

    if (width < 100) width = 100;
    if (height < 100) height = 100;

    view->x = x;
    view->y = y;
    wlr_scene_node_set_position(&view->scene_tree->node, x, y);
    wlr_xdg_toplevel_set_size(view->xdg_toplevel, width, height);
}

static void process_cursor_motion(struct lumiere_server *server, uint32_t time) {
    switch (server->cursor_mode) {
    case LUMIERE_CURSOR_MOVE:
        process_cursor_move(server, time);
        return;
    case LUMIERE_CURSOR_RESIZE:
        process_cursor_resize(server, time);
        return;
    case LUMIERE_CURSOR_PASSTHROUGH:
        break;
    }

    /* Normal cursor hareketi */
    double sx, sy;
    struct wlr_surface *surface = NULL;
    struct lumiere_view *view = desktop_view_at(
        server, server->cursor->x, server->cursor->y, &surface, &sx, &sy);

    if (!view) {
        wlr_cursor_set_xcursor(server->cursor, server->cursor_mgr, "default");
    }

    if (surface) {
        wlr_seat_pointer_notify_enter(server->seat, surface, sx, sy);
        wlr_seat_pointer_notify_motion(server->seat, time, sx, sy);
    } else {
        wlr_seat_pointer_clear_focus(server->seat);
    }
}

void cursor_motion(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, cursor_motion);
    struct wlr_pointer_motion_event *event = data;

    wlr_cursor_move(server->cursor, &event->pointer->base,
                    event->delta_x, event->delta_y);
    process_cursor_motion(server, event->time_msec);
}

void cursor_motion_absolute(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, cursor_motion_absolute);
    struct wlr_pointer_motion_absolute_event *event = data;

    wlr_cursor_warp_absolute(server->cursor, &event->pointer->base,
                             event->x, event->y);
    process_cursor_motion(server, event->time_msec);
}

void cursor_button(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, cursor_button);
    struct wlr_pointer_button_event *event = data;

    wlr_seat_pointer_notify_button(server->seat,
        event->time_msec, event->button, event->state);

    if (event->state == WL_POINTER_BUTTON_STATE_RELEASED) {
        server->cursor_mode = LUMIERE_CURSOR_PASSTHROUGH;
        return;
    }

    /* Tıklama ile odaklama */
    double sx, sy;
    struct wlr_surface *surface = NULL;
    struct lumiere_view *view = desktop_view_at(
        server, server->cursor->x, server->cursor->y, &surface, &sx, &sy);

    if (view) {
        focus_view(view, surface);
    }
}

void cursor_axis(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, cursor_axis);
    struct wlr_pointer_axis_event *event = data;

    wlr_seat_pointer_notify_axis(server->seat,
        event->time_msec, event->orientation, event->delta,
        event->delta_discrete, event->source, event->relative_direction);
}

void cursor_frame(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, cursor_frame);
    wlr_seat_pointer_notify_frame(server->seat);
}

/* ── Seat Requests ───────────────────────────────────────────── */

void seat_request_cursor(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, request_set_cursor);
    struct wlr_seat_pointer_request_set_cursor_event *event = data;

    struct wlr_seat_client *focused = server->seat->pointer_state.focused_client;
    if (focused == event->seat_client) {
        wlr_cursor_set_surface(server->cursor, event->surface,
                               event->hotspot_x, event->hotspot_y);
    }
}

void seat_request_set_selection(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, request_set_selection);
    struct wlr_seat_request_set_selection_event *event = data;
    wlr_seat_set_selection(server->seat, event->source, event->serial);
}
