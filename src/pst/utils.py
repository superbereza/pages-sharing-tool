"""Utility functions for pst."""

import hashlib
import secrets
import socket
import string
import subprocess
from pathlib import Path


def generate_page_id(length: int = 6) -> str:
    """Generate random page ID."""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_password(length: int = 6) -> str:
    """Generate random password (easy to type/dictate)."""
    # Avoid confusing characters: 0/O, 1/l/I
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str) -> str:
    """Hash password with SHA256."""
    return "sha256:" + hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    if not password_hash:
        return True  # No password required
    expected = hash_password(password)
    return secrets.compare_digest(expected, password_hash)


def get_external_ip(timeout: float = 2.0) -> str | None:
    """Get external IP via ifconfig.me."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), "ifconfig.me"],
            capture_output=True,
            text=True,
            timeout=timeout + 1,
        )
        if result.returncode == 0 and result.stdout.strip():
            ip = result.stdout.strip()
            # Basic validation
            if all(c in "0123456789." for c in ip):
                return ip
    except Exception:
        pass
    return None


def get_local_ip() -> str:
    """Get local network IP (not 127.0.0.1)."""
    try:
        # Connect to external address to find local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def detect_ip(host_override: str | None = None) -> str:
    """Detect best IP to use for URLs."""
    if host_override:
        return host_override

    # Try external IP first
    external = get_external_ip()
    if external:
        return external

    # Fall back to local IP
    return get_local_ip()


# Sensitive file patterns that should never be served
BLOCKED_PATTERNS = [
    ".env",           # .env, .env.local, .env.production, etc.
    ".git",           # .git/ directory
    ".ssh",           # SSH keys
    ".pem",           # Certificates
    ".key",           # Private keys
    ".secret",        # Secret files
    "credentials",    # Credentials files
    "__pycache__",    # Python cache
    ".venv",          # Python venv
    "venv",           # Python venv
    "node_modules",   # Node modules
    ".claude",        # Claude config
]


def is_sensitive_path(path: Path, base: Path) -> bool:
    """Check if path contains sensitive patterns."""
    try:
        relative = path.relative_to(base)
        parts = relative.parts
        name = path.name.lower()

        for pattern in BLOCKED_PATTERNS:
            # Check if any path component starts with pattern
            for part in parts:
                if part.lower().startswith(pattern):
                    return True
            # Also check the filename itself
            if name.startswith(pattern):
                return True

        return False
    except ValueError:
        return True  # If can't get relative path, treat as sensitive


def safe_path(base: Path, requested: str) -> Path | None:
    """
    Resolve path and ensure it's within base directory.
    Returns None if path is unsafe or sensitive.
    """
    try:
        base = base.resolve()
        # Normalize and resolve the requested path
        full_path = (base / requested).resolve()

        # Check path is within base
        if not full_path.is_relative_to(base):
            return None

        # Check symlinks don't escape
        if full_path.is_symlink():
            target = full_path.resolve()
            if not target.is_relative_to(base):
                return None

        # Block sensitive files
        if is_sensitive_path(full_path, base):
            return None

        return full_path
    except Exception:
        return None
