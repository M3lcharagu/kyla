"""Local-only helpers for user-directed sign-in and human-operated 2FA.

Credentials are never printed, persisted by these helpers, or submitted by an
automated login routine. Filling fields is an explicit caller action; the user
must review the page, submit it themselves, and complete any challenge visibly.
"""

from __future__ import annotations

import getpass
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class Credentials:
    """An in-memory username/password pair with a redacted representation."""

    username: str
    password: str

    def __repr__(self) -> str:
        return f"Credentials(username={self.username!r}, password='[REDACTED]')"


def prompt_credentials(
    *,
    input_fn: Callable[[str], str] = input,
    password_fn: Callable[[str], str] = getpass.getpass,
) -> Credentials:
    """Prompt locally; password input is masked by getpass where supported."""
    username = input_fn("Username: ").strip()
    password = password_fn("Password: ")
    if not username:
        raise ValueError("Username must not be empty")
    if not password:
        raise ValueError("Password must not be empty")
    return Credentials(username=username, password=password)


def load_local_credentials(path: Optional[str] = None) -> Credentials:
    """Read an explicitly local JSON file, refusing insecure POSIX permissions.

    The file must contain string keys ``username`` and ``password``. This
    helper never writes the file or sends credentials anywhere. On Windows,
    review the file's ACL yourself because POSIX mode checks are unavailable.
    """
    if path is None:
        source = Path.home() / ".config" / "kyla" / "web-agent" / "credentials.json"
    else:
        source = Path(path).expanduser()

    details = source.lstat()
    if not stat.S_ISREG(details.st_mode):
        raise ValueError("Credentials path must be a regular, non-symlink file")
    if os.name == "posix" and details.st_mode & 0o077:
        raise PermissionError("Credentials file must be private (POSIX mode 0600)")

    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Credentials file must be a JSON object")
    username, password = data.get("username"), data.get("password")
    if not isinstance(username, str) or not username.strip():
        raise ValueError("Credentials file must contain a non-empty username")
    if not isinstance(password, str) or not password:
        raise ValueError("Credentials file must contain a non-empty password")
    return Credentials(username=username, password=password)


def fill_login_fields(
    page: Any,
    username_selector: str,
    password_selector: str,
    credentials: Credentials,
) -> None:
    """Fill only the chosen fields; never click submit or infer page selectors."""
    page.locator(username_selector).fill(credentials.username)
    page.locator(password_selector).fill(credentials.password)


def wait_for_visible_2fa(
    page: Any,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    """Pause while the user completes a 2FA challenge in the visible browser."""
    if page.is_closed():
        raise RuntimeError("The browser page is closed")
    output_fn(
        "Complete the site's 2FA/security challenge in the visible browser. "
        "Do not paste a code here; press Enter here only after you finish."
    )
    input_fn("Waiting for your confirmation: ")
