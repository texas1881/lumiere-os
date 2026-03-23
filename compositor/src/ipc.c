/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          ✦ Lumière Compositor — IPC                          ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * Unix domain socket tabanlı IPC sistemi.
 * JSON formatında komut/yanıt.
 */

#include "server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <errno.h>

#define IPC_BUF_SIZE 4096

/* ── IPC Komut İşleme ────────────────────────────────────────── */

static void ipc_handle_command(struct lumiere_server *server,
                               int client_fd, const char *cmd) {
    char response[IPC_BUF_SIZE];

    if (strncmp(cmd, "get_workspaces", 14) == 0) {
        /* Workspace bilgilerini döndür */
        int len = snprintf(response, sizeof(response),
            "{\"active\":%d,\"count\":%d}",
            server->active_workspace,
            server->config.workspace_count);
        write(client_fd, response, len);
    }
    else if (strncmp(cmd, "get_views", 9) == 0) {
        /* Pencere listesini döndür */
        int len = snprintf(response, sizeof(response), "[");
        struct lumiere_view *view;
        bool first = true;
        wl_list_for_each(view, &server->views, link) {
            if (!first) {
                len += snprintf(response + len, sizeof(response) - len, ",");
            }
            const char *title = view->xdg_toplevel->title ?: "untitled";
            len += snprintf(response + len, sizeof(response) - len,
                "{\"title\":\"%s\",\"x\":%d,\"y\":%d,\"floating\":%s,\"workspace\":%d}",
                title, view->x, view->y,
                view->floating ? "true" : "false",
                view->workspace_id);
            first = false;
        }
        len += snprintf(response + len, sizeof(response) - len, "]");
        write(client_fd, response, len);
    }
    else if (strncmp(cmd, "workspace ", 10) == 0) {
        /* Workspace'e geç */
        int ws = atoi(cmd + 10);
        if (ws >= 0 && ws < 10) {
            server->active_workspace = ws;
            snprintf(response, sizeof(response),
                     "{\"ok\":true,\"workspace\":%d}", ws);
        } else {
            snprintf(response, sizeof(response),
                     "{\"ok\":false,\"error\":\"invalid workspace\"}");
        }
        write(client_fd, response, strlen(response));
    }
    else if (strncmp(cmd, "exec ", 5) == 0) {
        /* Komut çalıştır */
        const char *exec_cmd = cmd + 5;
        if (fork() == 0) {
            execl("/bin/sh", "/bin/sh", "-c", exec_cmd, NULL);
            _exit(1);
        }
        snprintf(response, sizeof(response), "{\"ok\":true}");
        write(client_fd, response, strlen(response));
    }
    else if (strcmp(cmd, "exit") == 0 || strcmp(cmd, "quit") == 0) {
        snprintf(response, sizeof(response), "{\"ok\":true,\"action\":\"exit\"}");
        write(client_fd, response, strlen(response));
        wl_display_terminate(server->wl_display);
    }
    else if (strcmp(cmd, "version") == 0) {
        snprintf(response, sizeof(response),
                 "{\"name\":\"lumiere-compositor\",\"version\":\"0.3.0\"}");
        write(client_fd, response, strlen(response));
    }
    else {
        snprintf(response, sizeof(response),
                 "{\"ok\":false,\"error\":\"unknown command\"}");
        write(client_fd, response, strlen(response));
    }
}

/* ── IPC Client Bağlantısı ───────────────────────────────────── */

static int ipc_client_handler(int fd, uint32_t mask, void *data) {
    struct lumiere_server *server = data;

    int client_fd = accept(fd, NULL, NULL);
    if (client_fd < 0) return 0;

    char buf[IPC_BUF_SIZE] = {0};
    ssize_t n = read(client_fd, buf, sizeof(buf) - 1);

    if (n > 0) {
        /* Trailing newline kaldır */
        while (n > 0 && (buf[n-1] == '\n' || buf[n-1] == '\r')) {
            buf[--n] = '\0';
        }
        ipc_handle_command(server, client_fd, buf);
    }

    close(client_fd);
    return 0;
}

/* ── IPC Init / Destroy ──────────────────────────────────────── */

bool ipc_init(struct lumiere_server *server) {
    const char *path = server->config.ipc_socket_path;

    /* Eski socket'i temizle */
    unlink(path);

    server->ipc_socket_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server->ipc_socket_fd < 0) {
        wlr_log(WLR_ERROR, "IPC socket oluşturulamadı: %s", strerror(errno));
        return false;
    }

    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, path, sizeof(addr.sun_path) - 1);

    if (bind(server->ipc_socket_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        wlr_log(WLR_ERROR, "IPC bind hatası: %s", strerror(errno));
        close(server->ipc_socket_fd);
        return false;
    }

    if (listen(server->ipc_socket_fd, 5) < 0) {
        wlr_log(WLR_ERROR, "IPC listen hatası: %s", strerror(errno));
        close(server->ipc_socket_fd);
        return false;
    }

    /* Event loop'a ekle */
    server->ipc_event_source = wl_event_loop_add_fd(
        server->wl_event_loop, server->ipc_socket_fd,
        WL_EVENT_READABLE, ipc_client_handler, server);

    setenv("LUMIERE_SOCKET", path, true);
    wlr_log(WLR_INFO, "✦ IPC socket: %s", path);

    return true;
}

void ipc_destroy(struct lumiere_server *server) {
    if (server->ipc_event_source) {
        wl_event_source_remove(server->ipc_event_source);
    }
    if (server->ipc_socket_fd > 0) {
        close(server->ipc_socket_fd);
        unlink(server->config.ipc_socket_path);
    }
}
