# ============================================================
# Lumière OS — Build System
# ============================================================

SHELL := /bin/bash
ISO_DIR := iso
BUILD_DIR := /tmp/lumiere-build
OUT_DIR := out
PROFILE := $(ISO_DIR)

.PHONY: help build-iso test-vm clean lint setup release check

help: ## Bu yardım mesajını göster
	@echo "╔══════════════════════════════════════════╗"
	@echo "║         ✦ Lumière OS Build System        ║"
	@echo "╚══════════════════════════════════════════╝"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build-iso: ## archiso ile ISO oluştur (root gerektirir)
	@echo "🔨 Lumière OS ISO oluşturuluyor..."
	@mkdir -p $(OUT_DIR)
	sudo mkarchiso -v -w $(BUILD_DIR) -o $(OUT_DIR) $(PROFILE)
	@echo "✅ ISO hazır: $(OUT_DIR)/"

test-vm: ## QEMU ile ISO'yu test et
	@echo "🖥️  Lumière OS VM'de başlatılıyor..."
	@ISO=$$(ls -t $(OUT_DIR)/*.iso 2>/dev/null | head -1); \
	if [ -z "$$ISO" ]; then \
		echo "❌ ISO bulunamadı. Önce 'make build-iso' çalıştırın."; \
		exit 1; \
	fi; \
	qemu-system-x86_64 \
		-enable-kvm \
		-m 2G \
		-cpu host \
		-smp 2 \
		-bios /usr/share/ovmf/x64/OVMF.fd \
		-cdrom "$$ISO" \
		-vga virtio \
		-display gtk

clean: ## Build dosyalarını temizle
	@echo "🧹 Temizleniyor..."
	sudo rm -rf $(BUILD_DIR)
	rm -rf $(OUT_DIR)
	@echo "✅ Temizlendi."

lint: ## Shell scriptlerini shellcheck ile kontrol et
	@echo "🔍 Shell scriptleri kontrol ediliyor..."
	@find . -name "*.sh" -exec shellcheck {} \;
	@echo "✅ Lint tamamlandı."

setup: ## Geliştirme bağımlılıklarını kur (Arch Linux)
	@echo "📦 Bağımlılıklar kuruluyor..."
	sudo pacman -S --needed archiso qemu-full ovmf shellcheck
	@echo "✅ Kurulum tamamlandı."

release: build-iso ## Release build (checksum ile)
	@echo "🚀 Release hazırlanıyor..."
	@cd $(OUT_DIR) && sha256sum *.iso > SHA256SUMS
	@cd $(OUT_DIR) && md5sum *.iso > MD5SUMS
	@echo "✅ Release hazır: $(OUT_DIR)/"
	@echo "  📀 ISO: $$(ls $(OUT_DIR)/*.iso)"
	@echo "  🔑 SHA256: $$(cat $(OUT_DIR)/SHA256SUMS)"

check: lint ## Tüm kontrolleri çalıştır (shell + yaml)
	@echo "🔍 YAML dosyaları kontrol ediliyor..."
	@if command -v yamllint &>/dev/null; then \
		yamllint -d "{extends: relaxed}" .github/workflows/*.yml 2>/dev/null || true; \
	fi
	@echo "✅ Tüm kontroller tamamlandı."

