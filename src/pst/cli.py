#!/usr/bin/env python3
"""
pst - Pages Sharing Tool

Securely publish static pages with password protection.

Examples:
    pst start                    # Start server
    pst add ./report.html        # Publish file
    pst add ./dist/              # Publish folder
    pst list                     # List pages
    pst remove abc123            # Remove page
    pst stop                     # Stop server
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path

from . import storage
from .utils import generate_page_id, generate_password, hash_password, detect_ip


def cmd_start(args: argparse.Namespace) -> int:
    """Start the server."""
    # Check if already running
    pid = storage.load_pid()
    if pid:
        try:
            os.kill(pid, 0)
            port = storage.load_port() or 8080
            host = storage.load_host() or detect_ip()
            print(f"Server already running: http://{host}:{port}")
            return 0
        except OSError:
            storage.clear_pid()

    port = args.port
    host = args.host or detect_ip()

    # Save config
    storage.save_port(port)
    if args.host:
        storage.save_host(args.host)

    # Start server in background
    cmd = [
        sys.executable, "-c",
        f"from pst.server import run_server; run_server(port={port})"
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
        return 0
    except OSError:
        print("Error: Server failed to start", file=sys.stderr)
        storage.clear_pid()
        return 1


def cmd_stop(args: argparse.Namespace) -> int:
    """Stop the server."""
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


def cmd_status(args: argparse.Namespace) -> int:
    """Show server status."""
    pid = storage.load_pid()
    port = storage.load_port() or 8080
    host = storage.load_host() or detect_ip()

    running = False
    if pid:
        try:
            os.kill(pid, 0)
            running = True
        except OSError:
            storage.clear_pid()

    if running:
        print(f"Server: http://{host}:{port} (running)")
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


def cmd_add(args: argparse.Namespace) -> int:
    """Add a page."""
    source = Path(args.path).resolve()
    if not source.exists():
        print(f"Error: {args.path} not found", file=sys.stderr)
        return 1

    page_id = generate_page_id()

    # Handle password
    if args.no_password:
        password = None
        password_hash = ""
    elif args.password:
        password = args.password
        password_hash = hash_password(password)
    else:
        password = generate_password()
        password_hash = hash_password(password)

    storage.add_page(page_id, source, password_hash)

    # Get URL
    port = storage.load_port() or 8080
    host = storage.load_host() or detect_ip()
    url = f"http://{host}:{port}/p/{page_id}/"

    print(f"Published: {url}")
    if password:
        print(f"Password: {password}")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all pages."""
    pages = storage.load_pages()
    if not pages:
        print("No pages published")
        return 0

    port = storage.load_port() or 8080
    host = storage.load_host() or detect_ip()

    for page_id, info in pages.items():
        url = f"http://{host}:{port}/p/{page_id}/"
        lock = "" if info["password_hash"] else " (public)"
        print(f"{url}{lock}")
        print(f"  Source: {info['source']}")

    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    """Remove a page."""
    if storage.remove_page(args.id):
        print(f"Removed: {args.id}")
        return 0
    else:
        print(f"Error: page {args.id} not found", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Securely publish static pages with password protection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start
    p_start = subparsers.add_parser("start", help="Start server")
    p_start.add_argument("--port", "-p", type=int, default=8080, help="Port (default: 8080)")
    p_start.add_argument("--host", help="Override auto-detected IP")
    p_start.set_defaults(func=cmd_start)

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop server")
    p_stop.set_defaults(func=cmd_stop)

    # status
    p_status = subparsers.add_parser("status", help="Show status")
    p_status.set_defaults(func=cmd_status)

    # add
    p_add = subparsers.add_parser("add", help="Publish a file or folder")
    p_add.add_argument("path", help="File or folder to publish")
    p_add.add_argument("--password", help="Custom password")
    p_add.add_argument("--no-password", action="store_true", help="No password (public)")
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = subparsers.add_parser("list", help="List published pages")
    p_list.set_defaults(func=cmd_list)

    # remove
    p_remove = subparsers.add_parser("remove", help="Remove a page")
    p_remove.add_argument("id", help="Page ID (or prefix)")
    p_remove.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
