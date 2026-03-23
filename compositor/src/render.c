/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          ✦ Lumière Compositor — Rendering                   ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * Output yönetimi ve scene graph rendering.
 */

#include "server.h"
#include <stdlib.h>
#include <time.h>

/* ── Output Frame ────────────────────────────────────────────── */
void output_frame(struct wl_listener *listener, void *data) {
    struct lumiere_output *output =
        wl_container_of(listener, output, frame);
    struct lumiere_server *server = output->server;
    struct wlr_scene *scene = server->scene;

    struct wlr_scene_output *scene_output =
        wlr_scene_get_scene_output(scene, output->wlr_output);

    /* Scene'i commit et */
    wlr_scene_output_commit(scene_output, NULL);

    /* Frame zamanlaması */
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    wlr_scene_output_send_frame_done(scene_output, &now);
}

/* ── Output Request State ────────────────────────────────────── */
void output_request_state(struct wl_listener *listener, void *data) {
    struct lumiere_output *output =
        wl_container_of(listener, output, request_state);
    const struct wlr_output_event_request_state *event = data;

    wlr_output_commit_state(output->wlr_output, event->state);
}

/* ── Output Destroy ──────────────────────────────────────────── */
void output_destroy(struct wl_listener *listener, void *data) {
    struct lumiere_output *output =
        wl_container_of(listener, output, destroy);

    wl_list_remove(&output->frame.link);
    wl_list_remove(&output->request_state.link);
    wl_list_remove(&output->destroy.link);
    wl_list_remove(&output->link);
    free(output);
}

/* ── Yeni Output (Monitör) ───────────────────────────────────── */
void server_new_output(struct wl_listener *listener, void *data) {
    struct lumiere_server *server =
        wl_container_of(listener, server, new_output);
    struct wlr_output *wlr_output = data;

    /* Renderer başlat */
    wlr_output_init_render(wlr_output, server->allocator, server->renderer);

    /* En iyi modu seç */
    struct wlr_output_state state;
    wlr_output_state_init(&state);
    wlr_output_state_set_enabled(&state, true);

    struct wlr_output_mode *mode = wlr_output_preferred_mode(wlr_output);
    if (mode != NULL) {
        wlr_output_state_set_mode(&state, mode);
    }

    wlr_output_commit_state(wlr_output, &state);
    wlr_output_state_finish(&state);

    /* Output struct */
    struct lumiere_output *output = calloc(1, sizeof(*output));
    output->wlr_output = wlr_output;
    output->server = server;

    /* Listeners */
    output->frame.notify = output_frame;
    wl_signal_add(&wlr_output->events.frame, &output->frame);

    output->request_state.notify = output_request_state;
    wl_signal_add(&wlr_output->events.request_state, &output->request_state);

    output->destroy.notify = output_destroy;
    wl_signal_add(&wlr_output->events.destroy, &output->destroy);

    wl_list_insert(&server->outputs, &output->link);

    /* Layout'a ekle */
    struct wlr_output_layout_output *l_output =
        wlr_output_layout_add_auto(server->output_layout, wlr_output);

    struct wlr_scene_output *scene_output =
        wlr_scene_output_create(server->scene, wlr_output);
    wlr_scene_output_layout_add_output(server->scene_layout,
                                       l_output, scene_output);

    wlr_log(WLR_INFO, "✦ Output eklendi: %s (%dx%d@%.1fHz)",
            wlr_output->name,
            mode ? mode->width : 0,
            mode ? mode->height : 0,
            mode ? mode->refresh / 1000.0f : 0);
}
