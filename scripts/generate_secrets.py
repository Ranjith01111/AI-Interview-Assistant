#!/usr/bin/env python3
"""
Generate secure random secrets for the AI Interview Assistant environment.

Copies .env.example to the target env file and replaces placeholder values
with cryptographically secure random strings. Existing real values are preserved.

Usage:
    python scripts/generate_secrets.py --env-file .env
    python scripts/generate_secrets.py --env-file .env.prod --force

After running, replace OPENROUTER_API_KEY / OPENAI_API_KEY with your real keys.
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_FILE = PROJECT_ROOT / ".env.example"

# ── Placeholder values that must be replaced ────────────────────────────
SECRETS = {
    "POSTGRES_PASSWORD": 32,       # hex
    "REDIS_PASSWORD": 32,          # hex
    "SECRET_KEY": 32,              # hex -> 64 chars
    "JWT_SECRET_KEY": 64,          # hex -> 128 chars
    "GRAFANA_PASSWORD": 32,        # hex
}


def generate_hex(nbytes: int) -> str:
    """Generate a cryptographically secure hex string."""
    return secrets.token_hex(nbytes)


def generate_env(target_path: Path, force: bool = False) -> None:
    """Create or update the env file, replacing placeholders with secrets."""

    if not EXAMPLE_FILE.exists():
        print(f"Error: template {EXAMPLE_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    target_path = Path(target_path).resolve()
    if target_path.exists() and not force:
        print(f"Error: {target_path} already exists. Use --force to overwrite non-secret lines.", file=sys.stderr)
        sys.exit(1)

    content = EXAMPLE_FILE.read_text(encoding="utf-8")
    lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()

        # Skip comments and blank lines as-is
        if not stripped or stripped.startswith("#"):
            lines.append(line)
            continue

        # Skip lines without an assignment
        if "=" not in stripped:
            lines.append(line)
            continue

        key, _, value = stripped.partition("=")
        if key in SECRETS and (target_path.exists() if not force else True):
            # Replace placeholder-looking values; keep existing real values unless --force
            placeholder_values = {
                "POSTGRES_PASSWORD": "REPLACE_ME_WITH_STRONG_PASSWORD",
                "REDIS_PASSWORD": "REPLACE_ME_WITH_STRONG_PASSWORD",
                "SECRET_KEY": "REPLACE_ME_WITH_64_HEX_CHARS",
                "JWT_SECRET_KEY": "REPLACE_ME_WITH_128_HEX_CHARS",
                "GRAFANA_PASSWORD": "REPLACE_ME_WITH_STRONG_PASSWORD",
            }

            current_value = value
            if not target_path.exists() or force or current_value == placeholder_values.get(key, current_value):
                line = f"{key}={generate_hex(SECRETS[key])}"
            else:
                # Preserve existing non-placeholder value when updating the file
                pass

        lines.append(line)

    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Set restrictive permissions on Unix systems
    try:
        target_path.chmod(0o600)
    except NotImplementedError:
        pass

    print(f"Generated secure env file: {target_path}")
    print("Remember to set OPENROUTER_API_KEY and OPENAI_API_KEY manually.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate secure environment secrets")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Target env file (default: .env)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing file (WARNING: will reset non-secret values too)",
    )

    args = parser.parse_args()
    generate_env(PROJECT_ROOT / args.env_file, force=args.force)
