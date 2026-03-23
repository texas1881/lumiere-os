/*
 * ╔══════════════════════════════════════════════════════════════╗
 * ║          ✦ Lumière Compositor — Entry Point                  ║
 * ╚══════════════════════════════════════════════════════════════╝
 */

#include "server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>

static void print_banner(void) {
    printf("\n");
    printf("  ╔══════════════════════════════════════╗\n");
    printf("  ║    ✦ Lumière Compositor v0.3.0       ║\n");
    printf("  ╚══════════════════════════════════════╝\n");
    printf("\n");
}

static void print_usage(const char *prog) {
    printf("Kullanım: %s [seçenekler]\n\n", prog);
    printf("  -c, --config <dosya>   Konfigürasyon dosyası\n");
    printf("  -d, --debug            Debug log seviyesi\n");
    printf("  -h, --help             Bu yardım mesajını göster\n");
    printf("  -v, --version          Versiyon bilgisi\n");
    printf("\n");
}

int main(int argc, char *argv[]) {
    char *config_path = NULL;
    enum wlr_log_importance log_level = WLR_ERROR;

    /* Komut satırı argümanları */
    static struct option long_options[] = {
        {"config",  required_argument, 0, 'c'},
        {"debug",   no_argument,       0, 'd'},
        {"help",    no_argument,       0, 'h'},
        {"version", no_argument,       0, 'v'},
        {0, 0, 0, 0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "c:dhv", long_options, NULL)) != -1) {
        switch (opt) {
        case 'c':
            config_path = strdup(optarg);
            break;
        case 'd':
            log_level = WLR_DEBUG;
            break;
        case 'h':
            print_usage(argv[0]);
            return 0;
        case 'v':
            printf("lumiere-compositor v0.3.0\n");
            return 0;
        default:
            print_usage(argv[0]);
            return 1;
        }
    }

    print_banner();
    wlr_log_init(log_level, NULL);

    /* Server başlat */
    struct lumiere_server server = {0};

    /* Konfigürasyon yükle */
    config_load_defaults(&server.config);
    if (config_path) {
        if (!config_load_file(&server.config, config_path)) {
            wlr_log(WLR_ERROR, "Konfigürasyon dosyası yüklenemedi: %s", config_path);
        }
        free(config_path);
    } else {
        /* Varsayılan yol */
        char default_path[512];
        const char *config_home = getenv("XDG_CONFIG_HOME");
        if (config_home) {
            snprintf(default_path, sizeof(default_path),
                     "%s/lumiere/compositor.conf", config_home);
        } else {
            snprintf(default_path, sizeof(default_path),
                     "%s/.config/lumiere/compositor.conf", getenv("HOME"));
        }
        config_load_file(&server.config, default_path);
    }

    /* Server init */
    if (!server_init(&server)) {
        wlr_log(WLR_ERROR, "Server başlatılamadı!");
        return 1;
    }

    /* IPC başlat */
    if (!ipc_init(&server)) {
        wlr_log(WLR_INFO, "IPC başlatılamadı, IPC devre dışı.");
    }

    /* Ana döngü */
    wlr_log(WLR_INFO, "✦ Lumière Compositor çalışıyor.");
    server_run(&server);

    /* Temizlik */
    ipc_destroy(&server);
    server_destroy(&server);

    wlr_log(WLR_INFO, "✦ Lumière Compositor kapatıldı.");
    return 0;
}
