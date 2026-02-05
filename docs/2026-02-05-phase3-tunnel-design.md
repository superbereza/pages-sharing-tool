# Phase 3: Tunnel Integration — Design Document

## Обзор

При запуске за NAT автоматически поднимаем cloudflared tunnel для каждого сервиса. Пользователь получает публичный URL без дополнительных действий.

### Ключевые решения

| Решение | Выбор |
|---------|-------|
| **Provider** | cloudflared (бесплатно, без регистрации) |
| **Когда** | Автоматически при NAT, с уведомлением |
| **Для чего** | Для drop server (8080) и каждого app на своём порту |
| **Установка** | install.sh качает binary в `~/.drop/bin/` |
| **Хранение URL** | В registry (pages.json) + `~/.drop/tunnel.json` для сервера |
| **Авторестарт** | Да, watchdog-тред каждые 10 секунд |

---

## Команды и UX

```bash
# VPS (публичный IP) — как сейчас, ничего не меняется
$ drop start
Server started: http://94.131.101.149:8080

# За NAT — автоматически поднимает tunnel
$ drop start
Detected NAT, starting tunnel...
Server started: https://random-words.trycloudflare.com
  (tunneled via cloudflared)

# App за NAT — тоже tunnel
$ drop start myapp
Detected NAT, starting tunnel...
App started: https://other-random.trycloudflare.com
  (tunneled via cloudflared)

# Явный opt-out
$ drop start --no-tunnel
Server started: http://192.168.1.50:8080 (local)

# Status показывает tunnel URLs
$ drop status
Server: https://random-words.trycloudflare.com (running, tunneled)

Pages:
  abc123  [app] [running]  https://other-random.trycloudflare.com (public)
  def456                   https://random-words.trycloudflare.com/p/def456/ (public)
```

---

## Установка cloudflared

**install.sh** — добавляем блок после systemd:

```bash
# Cloudflared (tunnel support)
CLOUDFLARED_BIN="$HOME/.drop/bin/cloudflared"
if ! command -v cloudflared &>/dev/null && [[ ! -f "$CLOUDFLARED_BIN" ]]; then
    echo "Installing cloudflared..."
    mkdir -p "$HOME/.drop/bin"
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)  CF_ARCH="amd64" ;;
        aarch64) CF_ARCH="arm64" ;;
        *)       CF_ARCH="amd64" ;;
    esac
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-${OS}-${CF_ARCH}" \
        -o "$CLOUDFLARED_BIN"
    chmod +x "$CLOUDFLARED_BIN"
    echo "  ✓ cloudflared"
fi
```

**При использовании** — `drop start` ищет cloudflared:
1. Сначала в PATH (`command -v cloudflared`)
2. Потом в `~/.drop/bin/cloudflared`
3. Если нет — "cloudflared not found. Run ./install.sh"

---

## NAT детекция и tunnel lifecycle

**Детекция** (уже есть в utils.py):
```python
external_ip = get_external_ip()   # curl ifconfig.me
local_ip = get_local_ip()         # socket
is_behind_nat = external_ip != local_ip
```

**Запуск tunnel:**
```python
# cloudflared tunnel --url http://localhost:8080 --no-autoupdate
# Выводит URL в stderr: "Your quick Tunnel has been created! Visit it at..."
# Парсим URL из stderr
```

**Авторестарт:** Отдельный watchdog-тред — проверяет что процесс cloudflared жив каждые 10 секунд. Если упал — перезапускает и обновляет URL в registry.

**Остановка:**
- `drop stop` — убивает все tunnel процессы + сервер
- `drop stop myapp` — убивает tunnel для этого app + app процесс

---

## Storage

**Registry (pages.json) — для apps:**
```json
{
  "abc123": {
    "type": "app",
    "source": "/path/to/app.py",
    "tunnel_url": "https://other-random.trycloudflare.com",
    "tunnel_pid": 12345,
    ...
  }
}
```

**Для сервера — `~/.drop/tunnel.json`:**
```json
{
  "url": "https://random-words.trycloudflare.com",
  "pid": 12345
}
```

---

## Границы

### Делаем
- Авто-tunnel при NAT с уведомлением
- Tunnel для drop server и каждого app
- Авторестарт tunnel при падении
- `--no-tunnel` opt-out
- Установка cloudflared через install.sh

### НЕ делаем
- Свой tunnel server (Drip и т.п.) — cloudflared quick tunnels достаточно
- Кеширование tunnel URL между рестартами — каждый раз новый
- Custom domains — это Phase 4 если понадобится
- Tunnel на VPS — только за NAT
