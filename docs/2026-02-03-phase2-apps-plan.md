# Phase 2: Apps Support — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add support for running web applications (Flask, FastAPI, Node) via `drop add --run --port` with proper lifecycle management.

**Architecture:** Extend existing registry with `type: "app"` entries. Apps run as child processes with PID tracking. Systemd integration for Linux auto-restart, fallback to simple background process on macOS.

**Tech Stack:** Python, Flask (existing), subprocess, systemd (Linux), no new dependencies.

---

## Phase 2a: Systemd Integration

### Task 1: Add systemd unit file generation to install.sh

**Files:**
- Modify: `install.sh`

**Step 1: Add systemd unit file creation**

After the skill symlink creation, add:

```bash
# Systemd integration (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SYSTEMD_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_DIR"

    cat > "$SYSTEMD_DIR/drop.service" << EOF
[Unit]
Description=Agent Instant Drop
After=network.target

[Service]
Type=simple
ExecStart=$VENV_DIR/bin/python -c "from drop.server import run_server; run_server()"
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

    echo "  ✓ systemd unit created"
    systemctl --user daemon-reload
fi
```

**Step 2: Test manually**

Run: `./install.sh`
Expected: On Linux, see "✓ systemd unit created"

Run: `cat ~/.config/systemd/user/drop.service`
Expected: Unit file with correct ExecStart path

**Step 3: Commit**

```bash
git add install.sh
git commit -m "feat: add systemd unit file generation for Linux"
```

---

### Task 2: Add systemd cleanup to uninstall.sh

**Files:**
- Modify: `uninstall.sh`

**Step 1: Read current uninstall.sh**

Read the file first.

**Step 2: Add systemd cleanup before removing files**

Add after the initial checks:

```bash
# Stop and disable systemd service (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if systemctl --user is-active drop.service &>/dev/null; then
        echo "Stopping systemd service..."
        systemctl --user stop drop.service
    fi
    if systemctl --user is-enabled drop.service &>/dev/null; then
        echo "Disabling systemd service..."
        systemctl --user disable drop.service
    fi
    UNIT_FILE="$HOME/.config/systemd/user/drop.service"
    if [[ -f "$UNIT_FILE" ]]; then
        echo "Removing systemd unit..."
        rm "$UNIT_FILE"
        systemctl --user daemon-reload
    fi
fi
```

**Step 3: Test manually**

Run: `./uninstall.sh` (on Linux)
Expected: Stops service, removes unit file

**Step 4: Commit**

```bash
git add uninstall.sh
git commit -m "feat: add systemd cleanup to uninstall script"
```

---

### Task 3: Add platform detection to utils.py

**Files:**
- Modify: `src/drop/utils.py`

**Step 1: Add platform detection function**

Add at the end of utils.py:

```python
import platform


def has_systemd() -> bool:
    """Check if systemd is available (Linux with systemd user services)."""
    if platform.system() != "Linux":
        return False
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-system-running"],
            capture_output=True,
            timeout=2,
        )
        # Returns 0 for running, or other codes but command exists
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

**Step 2: Test manually**

Run: `python -c "from drop.utils import has_systemd; print(has_systemd())"`
Expected: `True` on Linux with systemd, `False` otherwise

**Step 3: Commit**

```bash
git add src/drop/utils.py
git commit -m "feat: add systemd detection utility"
```

---

### Task 4: Refactor cmd_start to use systemd when available

**Files:**
- Modify: `src/drop/cli.py`

**Step 1: Add import**

Add to imports:

```python
from .utils import generate_page_id, generate_password, hash_password, detect_ip, load_manifest, MANIFEST_FILE, has_systemd
```

**Step 2: Create helper function for systemd start**

Add before `cmd_start`:

```python
def _start_with_systemd(port: int, host: str) -> int:
    """Start server using systemd."""
    # Update unit file with current port
    unit_path = Path.home() / ".config/systemd/user/drop.service"
    if not unit_path.exists():
        print("Error: systemd unit not found. Run ./install.sh", file=sys.stderr)
        return 1

    # Read and update ExecStart with port
    content = unit_path.read_text()
    # Replace the run_server() call to include port
    import re
    new_content = re.sub(
        r'run_server\([^)]*\)',
        f'run_server(port={port})',
        content
    )
    unit_path.write_text(new_content)

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "drop.service"], check=True)
    subprocess.run(["systemctl", "--user", "start", "drop.service"], check=True)

    # Wait and verify
    time.sleep(1)
    result = subprocess.run(
        ["systemctl", "--user", "is-active", "drop.service"],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() == "active":
        print(f"Server started: http://{host}:{port}")
        print("  (systemd managed, auto-restart enabled)")
        return 0
    else:
        print("Error: Server failed to start", file=sys.stderr)
        return 1


def _stop_with_systemd() -> int:
    """Stop server using systemd."""
    subprocess.run(["systemctl", "--user", "stop", "drop.service"])
    subprocess.run(["systemctl", "--user", "disable", "drop.service"])
    print("Server stopped")
    return 0
```

**Step 3: Update cmd_start to use systemd**

Replace `cmd_start` function:

```python
def cmd_start(args: argparse.Namespace) -> int:
    """Start the server."""
    port = args.port
    host = args.host or detect_ip()

    # Save config
    storage.save_port(port)
    if args.host:
        storage.save_host(args.host)

    # Check if already running (systemd or PID)
    if has_systemd():
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "drop.service"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() == "active":
            print(f"Server already running: http://{host}:{port}")
            return 0
        return _start_with_systemd(port, host)

    # Fallback: PID-based management
    pid = storage.load_pid()
    if pid:
        try:
            os.kill(pid, 0)
            print(f"Server already running: http://{host}:{port}")
            return 0
        except OSError:
            storage.clear_pid()

    # Start server in background
    cmd = [
        sys.executable, "-c",
        f"from drop.server import run_server; run_server(port={port})"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    storage.save_pid(proc.pid)

    # Wait a moment and check it started
    time.sleep(0.5)
    try:
        os.kill(proc.pid, 0)
        print(f"Server started: http://{host}:{port}")
        print("  ⚠️  No systemd — auto-restart disabled")
        return 0
    except OSError:
        print("Error: Server failed to start", file=sys.stderr)
        storage.clear_pid()
        return 1
```

**Step 4: Update cmd_stop to use systemd**

Replace `cmd_stop` function:

```python
def cmd_stop(args: argparse.Namespace) -> int:
    """Stop the server."""
    if has_systemd():
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "drop.service"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() == "active":
            return _stop_with_systemd()
        print("Server not running")
        return 0

    # Fallback: PID-based
    pid = storage.load_pid()
    if not pid:
        print("Server not running")
        return 0

    try:
        os.kill(pid, signal.SIGTERM)
        print("Server stopped")
    except OSError:
        print("Server was not running")

    storage.clear_pid()
    return 0
```

**Step 5: Update cmd_status for systemd awareness**

Update the running check in `cmd_status`:

```python
def cmd_status(args: argparse.Namespace) -> int:
    """Show server status."""
    port = storage.load_port() or 8080
    host = storage.load_host() or detect_ip()

    running = False
    systemd_managed = False

    if has_systemd():
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "drop.service"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip() == "active":
            running = True
            systemd_managed = True
    else:
        pid = storage.load_pid()
        if pid:
            try:
                os.kill(pid, 0)
                running = True
            except OSError:
                storage.clear_pid()

    if running:
        extra = " (systemd)" if systemd_managed else ""
        print(f"Server: http://{host}:{port} (running{extra})")
    else:
        print("Server: not running")

    print()
    pages = storage.load_pages()
    if not pages:
        print("No pages published")
    else:
        print("Pages:")
        for page_id, info in pages.items():
            source = info["source"]
            created = datetime.fromisoformat(info["created_at"])
            age = datetime.now(UTC) - created
            if age.days > 0:
                age_str = f"{age.days}d ago"
            elif age.seconds > 3600:
                age_str = f"{age.seconds // 3600}h ago"
            else:
                age_str = f"{age.seconds // 60}m ago"

            lock = "" if info["password_hash"] else " (public)"
            print(f"  {page_id}  {source}  {age_str}{lock}")

    return 0
```

**Step 6: Test manually**

Run: `drop stop && drop start`
Expected: On Linux with systemd, see "(systemd managed, auto-restart enabled)"

Run: `drop status`
Expected: Shows "(running (systemd))"

Run: `drop stop`
Expected: Stops and disables service

**Step 7: Commit**

```bash
git add src/drop/cli.py
git commit -m "feat: use systemd for server lifecycle on Linux"
```

---

## Phase 2b: Apps Support

### Task 5: Extend storage.py with app fields

**Files:**
- Modify: `src/drop/storage.py`

**Step 1: Update PageInfo TypedDict**

Replace `PageInfo` with:

```python
class PageInfo(TypedDict):
    source: str
    is_dir: bool
    password_hash: str  # Empty string if no password
    created_at: str
    description: str  # Optional description
    name: str  # URL slug (human-readable name)
    # App-specific fields (optional)
    type: str  # "static" or "app"
    run_cmd: str  # Command to run (for apps)
    port: int  # App port (for apps)
    pid: int  # Running process PID (for apps, 0 if not running)
```

**Step 2: Update add_page function**

Replace `add_page`:

```python
def add_page(
    page_id: str,
    source: Path,
    password_hash: str,
    description: str = "",
    name: str = "",
    page_type: str = "static",
    run_cmd: str = "",
    port: int = 0,
) -> None:
    """Add a page to registry."""
    pages = load_pages()
    pages[page_id] = {
        "source": str(source.resolve()),
        "is_dir": source.is_dir(),
        "password_hash": password_hash,
        "created_at": datetime.now(UTC).isoformat(),
        "description": description,
        "name": name,
        "type": page_type,
        "run_cmd": run_cmd,
        "port": port,
        "pid": 0,
    }
    save_pages(pages)
```

**Step 3: Add functions to update app PID**

Add after `get_full_page_id`:

```python
def update_page_pid(page_id: str, pid: int) -> bool:
    """Update running PID for an app. Returns True if found."""
    pages = load_pages()
    full_id = get_full_page_id(page_id)
    if not full_id:
        return False
    pages[full_id]["pid"] = pid
    save_pages(pages)
    return True


def get_app_status(page_id: str) -> str:
    """Get app status: 'running', 'stopped', or 'crashed'."""
    page = get_page(page_id)
    if not page or page.get("type") != "app":
        return "not_app"

    pid = page.get("pid", 0)
    if pid == 0:
        return "stopped"

    import os
    try:
        os.kill(pid, 0)
        return "running"
    except OSError:
        return "crashed"
```

**Step 4: Test manually**

Run: `python -c "from drop.storage import PageInfo; print(PageInfo.__annotations__)"`
Expected: Shows all fields including type, run_cmd, port, pid

**Step 5: Commit**

```bash
git add src/drop/storage.py
git commit -m "feat: extend storage with app-specific fields"
```

---

### Task 6: Add --run and --port flags to cmd_add

**Files:**
- Modify: `src/drop/cli.py`

**Step 1: Update argparse for add command**

In `main()`, update `p_add`:

```python
    # add
    p_add = subparsers.add_parser("add", help="Publish a file or folder")
    p_add.add_argument("path", help="File or folder to publish")
    p_add.add_argument("--name", "-n", help="Human-readable name for URL (slug)")
    p_add.add_argument("--password", "-p", nargs="?", const=True, default=None,
                       help="Protect with password (auto-generate if no value given)")
    p_add.add_argument("--desc", "-d", help="Description for listing")
    p_add.add_argument("--run", "-r", help="Command to run (makes this an app)")
    p_add.add_argument("--port", type=int, help="Port the app listens on (required with --run)")
    p_add.set_defaults(func=cmd_add)
```

**Step 2: Update cmd_add to handle apps**

Replace `cmd_add`:

```python
def cmd_add(args: argparse.Namespace) -> int:
    """Add a page or app."""
    source = Path(args.path).resolve()
    if not source.exists():
        print(f"Error: {args.path} not found", file=sys.stderr)
        return 1

    # Validate app args
    is_app = bool(args.run)
    if is_app and not args.port:
        print("Error: --port is required when using --run", file=sys.stderr)
        return 1
    if args.port and not args.run:
        print("Error: --run is required when using --port", file=sys.stderr)
        return 1

    # Directory requires manifest (for static only)
    if source.is_dir() and not is_app:
        manifest = load_manifest(source)
        if manifest is None:
            print(f"Error: Directory requires {MANIFEST_FILE} manifest", file=sys.stderr)
            print(f"Create {source / MANIFEST_FILE} with allowed file patterns:", file=sys.stderr)
            print("  index.html", file=sys.stderr)
            print("  assets/**", file=sys.stderr)
            return 1
        print(f"Using manifest: {', '.join(manifest)}")

    page_id = generate_page_id()

    # Handle password (default: no password)
    if args.password:
        password = args.password if args.password is not True else generate_password()
        password_hash = hash_password(password)
    else:
        password = None
        password_hash = ""

    name = args.name or ""

    # Add to storage
    storage.add_page(
        page_id,
        source,
        password_hash,
        args.desc or "",
        name,
        page_type="app" if is_app else "static",
        run_cmd=args.run or "",
        port=args.port or 0,
    )

    # Get URL
    server_port = storage.load_port() or 8080
    host = storage.load_host() or detect_ip()

    if is_app:
        # App URL is direct port access
        url = f"http://{host}:{args.port}/"
        print(f"App registered: {url}")
        print(f"Run 'drop start {page_id}' to start the app")
    else:
        # Static URL through drop server
        if name:
            url = f"http://{host}:{server_port}/p/{page_id}/{name}/"
        else:
            url = f"http://{host}:{server_port}/p/{page_id}/"
        print(f"Published: {url}")

    if password:
        print(f"Password: {password}")

    return 0
```

**Step 3: Test manually**

Run: `drop add ./test.py --run "python test.py" --port 5000 --name myapp`
Expected: "App registered: http://...:5000/"

Run: `drop list --all`
Expected: Shows the app entry

**Step 4: Commit**

```bash
git add src/drop/cli.py
git commit -m "feat: add --run and --port flags for app support"
```

---

### Task 7: Add app lifecycle commands (start/stop by name)

**Files:**
- Modify: `src/drop/cli.py`

**Step 1: Add cmd_start_app function**

Add after `_stop_with_systemd`:

```python
def cmd_start_app(args: argparse.Namespace) -> int:
    """Start an app by name/ID."""
    page = storage.get_page(args.name)
    if not page:
        print(f"Error: '{args.name}' not found", file=sys.stderr)
        return 1

    if page.get("type") != "app":
        print(f"Error: '{args.name}' is not an app (use 'drop start' for server)", file=sys.stderr)
        return 1

    # Check if already running
    status = storage.get_app_status(args.name)
    if status == "running":
        host = storage.load_host() or detect_ip()
        print(f"App already running: http://{host}:{page['port']}/")
        return 0

    # Start the app
    source_dir = Path(page["source"]).parent if not Path(page["source"]).is_dir() else Path(page["source"])
    run_cmd = page["run_cmd"]

    proc = subprocess.Popen(
        run_cmd,
        shell=True,
        cwd=source_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Save PID
    full_id = storage.get_full_page_id(args.name)
    storage.update_page_pid(full_id, proc.pid)

    # Wait and verify
    time.sleep(1)
    try:
        os.kill(proc.pid, 0)
        host = storage.load_host() or detect_ip()
        print(f"App started: http://{host}:{page['port']}/")
        return 0
    except OSError:
        storage.update_page_pid(full_id, 0)
        print("Error: App failed to start", file=sys.stderr)
        return 1


def cmd_stop_app(args: argparse.Namespace) -> int:
    """Stop an app by name/ID."""
    page = storage.get_page(args.name)
    if not page:
        print(f"Error: '{args.name}' not found", file=sys.stderr)
        return 1

    if page.get("type") != "app":
        print(f"Error: '{args.name}' is not an app (use 'drop stop' for server)", file=sys.stderr)
        return 1

    status = storage.get_app_status(args.name)
    if status != "running":
        print(f"App not running")
        return 0

    pid = page.get("pid", 0)
    try:
        os.kill(pid, signal.SIGTERM)
        print("App stopped")
    except OSError:
        print("App was not running")

    full_id = storage.get_full_page_id(args.name)
    storage.update_page_pid(full_id, 0)
    return 0
```

**Step 2: Update cmd_start to route to app start**

Update `cmd_start` to check for app name:

At the beginning of `cmd_start`, add:

```python
def cmd_start(args: argparse.Namespace) -> int:
    """Start the server or an app."""
    # If name provided, start app instead
    if hasattr(args, 'name') and args.name:
        return cmd_start_app(args)

    # ... rest of existing code
```

**Step 3: Update argparse to support `drop start <name>`**

Update the start parser in `main()`:

```python
    # start
    p_start = subparsers.add_parser("start", help="Start server or app")
    p_start.add_argument("name", nargs="?", help="App name/ID to start (omit for server)")
    p_start.add_argument("--port", "-p", type=int, default=8080, help="Server port (default: 8080)")
    p_start.add_argument("--host", help="Override auto-detected IP")
    p_start.set_defaults(func=cmd_start)

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop server or app")
    p_stop.add_argument("name", nargs="?", help="App name/ID to stop (omit for server)")
    p_stop.set_defaults(func=cmd_stop)
```

**Step 4: Update cmd_stop to route to app stop**

Update `cmd_stop`:

```python
def cmd_stop(args: argparse.Namespace) -> int:
    """Stop the server or an app."""
    # If name provided, stop app instead
    if hasattr(args, 'name') and args.name:
        return cmd_stop_app(args)

    # ... rest of existing code
```

**Step 5: Test manually**

Run: `drop add ./app.py --run "python app.py" --port 5000 --name testapp`
Run: `drop start testapp`
Expected: "App started: http://...:5000/"

Run: `drop stop testapp`
Expected: "App stopped"

**Step 6: Commit**

```bash
git add src/drop/cli.py
git commit -m "feat: add app lifecycle commands (start/stop by name)"
```

---

### Task 8: Update cmd_list to show app status

**Files:**
- Modify: `src/drop/cli.py`

**Step 1: Update cmd_list output**

Replace `cmd_list`:

```python
def cmd_list(args: argparse.Namespace) -> int:
    """List pages (filtered by current directory by default)."""
    pages = storage.load_pages()
    if not pages:
        print("No pages published")
        return 0

    server_port = storage.load_port() or 8080
    host = storage.load_host() or detect_ip()
    cwd = Path.cwd().resolve()

    # Filter by current directory unless --all
    if not args.all:
        filtered = {}
        for page_id, info in pages.items():
            source = Path(info["source"])
            try:
                if source.is_relative_to(cwd):
                    filtered[page_id] = info
            except (ValueError, OSError):
                pass
        pages = filtered

    if not pages:
        print(f"No pages from {cwd}")
        print("Use 'drop list --all' to see all pages")
        return 0

    for page_id, info in pages.items():
        page_type = info.get("type", "static")
        name = info.get("name", "")

        if page_type == "app":
            # App: show direct port URL
            port = info.get("port", 0)
            url = f"http://{host}:{port}/"
            status = storage.get_app_status(page_id)
            status_str = f" [{status}]"
        else:
            # Static: show drop server URL
            if name:
                url = f"http://{host}:{server_port}/p/{page_id}/{name}/"
            else:
                url = f"http://{host}:{server_port}/p/{page_id}/"
            status_str = ""

        lock = "" if info["password_hash"] else " (public)"

        # Check source exists
        source_exists = Path(info["source"]).exists()
        source_warning = " ⚠️ source deleted" if not source_exists else ""

        type_label = f"[{page_type}]" if page_type == "app" else ""
        print(f"{page_id[:8]}  {type_label}{status_str}  {url}{lock}{source_warning}")

        desc = info.get("description", "")
        if desc:
            print(f"  {desc}")
        print(f"  Source: {info['source']}")
        if page_type == "app":
            print(f"  Run: {info.get('run_cmd', '')}")

    return 0
```

**Step 2: Test manually**

Run: `drop list --all`
Expected: Shows apps with [app] label and [running/stopped/crashed] status

**Step 3: Commit**

```bash
git add src/drop/cli.py
git commit -m "feat: show app type and status in list output"
```

---

### Task 9: Add cleanup command

**Files:**
- Modify: `src/drop/cli.py`

**Step 1: Add cmd_cleanup function**

Add after `cmd_remove`:

```python
def cmd_cleanup(args: argparse.Namespace) -> int:
    """Remove entries with deleted source files."""
    pages = storage.load_pages()
    if not pages:
        print("No pages to clean")
        return 0

    removed = []
    for page_id, info in list(pages.items()):
        source = Path(info["source"])
        if not source.exists():
            # Stop app if running
            if info.get("type") == "app":
                pid = info.get("pid", 0)
                if pid:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except OSError:
                        pass
            removed.append(page_id)
            del pages[page_id]

    if removed:
        storage.save_pages(pages)
        for page_id in removed:
            print(f"Removed: {page_id} (source deleted)")
        print(f"Cleaned {len(removed)} stale entries")
    else:
        print("No stale entries found")

    return 0
```

**Step 2: Add cleanup to argparse**

In `main()`, add after remove parser:

```python
    # cleanup
    p_cleanup = subparsers.add_parser("cleanup", help="Remove entries with deleted sources")
    p_cleanup.set_defaults(func=cmd_cleanup)
```

**Step 3: Test manually**

Run: `drop cleanup`
Expected: "No stale entries found" or removes stale entries

**Step 4: Commit**

```bash
git add src/drop/cli.py
git commit -m "feat: add cleanup command for stale entries"
```

---

### Task 10: Update skill documentation

**Files:**
- Modify: `skills/drop.md`

**Step 1: Read current skill file**

Read the file first.

**Step 2: Update with app examples**

Add app examples to the skill documentation, including:
- `drop add ./app.py --run "flask run --port 5000" --port 5000 --name api`
- `drop start api`
- `drop stop api`
- Updated `drop list` output showing app status

**Step 3: Commit**

```bash
git add skills/drop.md
git commit -m "docs: update skill with app support examples"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| **2a** | 1-4 | Systemd integration for auto-restart |
| **2b** | 5-10 | Apps support with --run/--port and lifecycle |

After completing all tasks:
- `drop start` uses systemd on Linux (auto-restart)
- `drop add --run "cmd" --port N` registers apps
- `drop start <name>` / `drop stop <name>` controls apps
- `drop list` shows app status (running/stopped/crashed)
- `drop cleanup` removes stale entries
