# Phase 2: Apps Support — Design Document

## Обзор

Расширить drop для запуска приложений (Flask, FastAPI, Node и др.) с тем же UX что и для статики.

### Подфазы

| Подфаза | Что делаем | Статус |
|---------|------------|--------|
| **2a** | Systemd интеграция (Linux) + fallback (macOS) | ✅ Done |
| **2b** | Apps: `--run` + `--port`, lifecycle (start/stop) | ✅ Done |
| **2c** | Proxy через единый порт | ❌ Cancelled (over-engineering) |
| **Phase 3** | ngrok интеграция | 🔜 Next |

---

## Команды

```bash
# Сервер
drop start                  # запустить (systemd enable+start или fallback)
drop stop                   # остановить (systemd stop+disable)
drop status                 # статус + warnings

# Публикация
drop add ./file --name x                              # static
drop add ./app --name x --run "cmd" --port N          # app
drop remove <name>                                     # удалить

# Lifecycle apps
drop start <name>           # запустить остановленный app
drop stop <name>            # остановить app

# Информация
drop list                   # все со статусами
drop cleanup                # удалить stale (source deleted)
```

---

## Apps: простая модель

Без автодетекта типа. Два флага:
- `--run "команда"` — как запускать
- `--port N` — на каком порту слушает

### Примеры

```bash
# Static (как сейчас)
drop add ./page.html --name landing

# Flask
drop add ./app.py --name api --run "flask run --port 5000" --port 5000

# FastAPI
drop add ./app.py --name api --run "uvicorn app:app --port 8000" --port 8000

# Node/Express
drop add ./project --name web --run "PORT=3000 node app.js" --port 3000

# Next.js
drop add ./project --name web --run "npm run dev -- --port 3000" --port 3000
```

### Что делает drop

1. Запускает `--run` команду как есть
2. Сохраняет `--port` в registry
3. Показывает URL `http://host:port/`

---

## Registry

```json
{
  "abc123": {
    "type": "static",
    "source": "/path/to/page.html",
    "name": "landing",
    "password_hash": "",
    "created_at": "2026-02-03T..."
  },
  "def456": {
    "type": "app",
    "source": "/path/to/app.py",
    "name": "api",
    "run": "flask run --port 5000",
    "port": 5000,
    "pid": 12345,
    "created_at": "2026-02-03T..."
  }
}
```

---

## Systemd интеграция

### Linux (полный функционал)

```bash
drop start   # systemctl --user enable drop + start
drop stop    # systemctl --user stop drop + disable
```

Unit file создаётся при `./install.sh`:
```ini
# ~/.config/systemd/user/drop.service
[Unit]
Description=Agent Instant Drop

[Service]
ExecStart=/home/user/.local/bin/drop serve
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

### macOS (fallback)

```bash
drop start   # просто запускает процесс в background
drop stop    # останавливает процесс
```

Warning при старте:
```
Warning: systemd not found, auto-restart disabled
Server started: http://...
```

---

## NAT детекция

При `drop start` проверяем публичный ли IP:

```python
external_ip = get_external_ip()  # curl ifconfig.me
local_ip = get_local_ip()        # socket

if external_ip == local_ip:
    # Публичный IP
else:
    # За NAT
```

### Вывод

```bash
# Публичный IP (VPS)
$ drop start
Server started: http://94.131.101.149:8080

# За NAT (ноутбук)
$ drop start
⚠️  Behind NAT — URLs work only in local network
    External: 94.131.101.149 (not directly accessible)
    Local:    192.168.1.50

    For public access: ngrok http 8080

Server started: http://192.168.1.50:8080 (local)
```

---

## Проверка существования source

При `drop list` / `drop status` проверяем существует ли source файл:

```bash
$ drop list
landing   static   http://...                    ✓
api       app      http://...:5000/              ✓ running
old-page  static   http://...                    ⚠️ source deleted

$ drop cleanup
Removing old-page (source deleted)
Removed 1 stale entry
```

---

## Логи приложений

Не управляем. App сам разбирается с логированием.

Если app упал и непонятно почему — агент запускает вручную и смотрит вывод.

---

## Crash handling

При падении app — просто статус "crashed":

```bash
$ drop list
api    app    crashed (exit code 1)
```

Агент делает `drop start api` чтобы поднять.

Авто-рестарт apps — не в MVP.

---

## Порты

Apps на своих портах (указывается через `--port`).

Proxy через единый порт 8080 — Phase 2c (позже).

---

## Границы

### Можем показать
- Статичные файлы (HTML, CSS, JS, картинки)
- Python веб-апы (Flask, FastAPI, Django, Streamlit)
- Node веб-апы (Express, Next.js, Vite)
- Любой HTTP сервер

### Не можем показать
- Desktop GUI (Qt, Tkinter) — нет HTTP
- CLI утилиты — нет визуального вывода
- Мобильные приложения — нужен эмулятор

---

## Отложено

### Phase 2c: Proxy — ОТМЕНЕНО (over-engineering)

**Идея:** Единый порт для всего:
```
http://host:8080/p/abc/landing/   → статика
http://host:8080/p/def/api/       → proxy → Flask:5000
```

**Вердикт:** Over-engineering. Текущая реализация (apps на своих портах) достаточна для use case drop — временные прототипы для показа человеку. Открыть дополнительный порт на VPS не проблема. Proxy добавляет сложность (WebSocket, URL rewriting) без реальной пользы.

---

### Phase 3: ngrok — СЛЕДУЮЩИЙ ШАГ

**Проблема:** За NAT на ноутбуке нельзя показать результат человеку на другой машине.

**Решение:**
```bash
drop start --tunnel  # публичный URL через ngrok/cloudflared
```

**Статус:** В работе.

---

### Backlog
См. `docs/backlog.md`
