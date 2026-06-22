"""Server-side input hardening for the Haku backend.

The frontend lets the user pick arbitrary output/input folders via a native
folder dialog, so we cannot pin a single fixed root. What we *can* enforce:

- A user-supplied ``filename`` must be a bare basename (no ``/`` ``\\`` ``..``),
  so the written file is always contained inside the chosen directory.
- A user-supplied directory must resolve to a real, existing directory and,
  when ``HAKU_ALLOWED_ROOTS`` is set, must live under one of those roots.
- A user-supplied image URL (``/process/from-url``) must use http(s) and must
  not resolve to a private, loopback, or link-local address (SSRF guard).

Set ``HAKU_ALLOWED_ROOTS`` to an ``os.pathsep``-separated list of directories
to additionally constrain where files may be read/written.
"""

import ipaddress
import os
import re
import socket
from pathlib import Path
from urllib.parse import urlsplit

# Bare filename: letters, digits, space, dot, underscore, hyphen, parens.
# No path separators, no "..", no drive letters, no control chars.
_FILENAME_RE = re.compile(r"^[A-Za-z0-9 ._()\-]+$")


class PathValidationError(ValueError):
    """Raised when a path or filename fails server-side validation."""


def _allowed_roots() -> list[Path]:
    raw = os.environ.get("HAKU_ALLOWED_ROOTS", "")
    roots: list[Path] = []
    for part in raw.split(os.pathsep):
        part = part.strip()
        if part:
            try:
                roots.append(Path(part).resolve(strict=False))
            except (OSError, ValueError):
                continue
    return roots


def safe_filename(name: str) -> str:
    """Return ``name`` if it is a safe bare filename, else raise.

    Rejects empty names, path separators, parent refs (``..``), absolute
    paths, NUL bytes, and reserved single/double dot names.
    """
    if not name or not isinstance(name, str):
        raise PathValidationError("filename must be a non-empty string")
    if "\x00" in name:
        raise PathValidationError("filename contains a NUL byte")
    # os.path.basename strips any directory part; if it differs, the caller
    # smuggled separators or a parent ref.
    if name != os.path.basename(name):
        raise PathValidationError(f"filename must not contain a path: {name!r}")
    if name in (".", ".."):
        raise PathValidationError("filename must not be '.' or '..'")
    if not _FILENAME_RE.match(name):
        raise PathValidationError(f"filename has disallowed characters: {name!r}")
    return name


def validate_dir(dir_path: str) -> Path:
    """Resolve ``dir_path``, ensure it is an existing directory, and (if
    ``HAKU_ALLOWED_ROOTS`` is configured) that it lives under an allowed root.

    Returns the resolved :class:`~pathlib.Path`.
    """
    if not dir_path or not isinstance(dir_path, str):
        raise PathValidationError("directory must be a non-empty string")
    if "\x00" in dir_path:
        raise PathValidationError("directory contains a NUL byte")

    try:
        resolved = Path(dir_path).resolve(strict=False)
    except (OSError, ValueError) as exc:
        raise PathValidationError(f"invalid directory: {dir_path!r}") from exc

    if not resolved.is_dir():
        raise PathValidationError(f"not an existing directory: {dir_path!r}")

    roots = _allowed_roots()
    if roots and not any(_is_within(resolved, root) for root in roots):
        raise PathValidationError(
            f"directory {dir_path!r} is outside the allowed roots"
        )

    return resolved


def safe_output_path(dir_path: str, filename: str, suffix: str = "") -> Path:
    """Validate ``dir_path`` and ``filename`` and return the contained path.

    ``suffix`` (e.g. ``".png"``) is appended to the validated basename. The
    final path is re-checked with :func:`_is_within` so it can never escape the
    validated directory even after normalization.
    """
    base = validate_dir(dir_path)
    name = safe_filename(filename + suffix) if suffix else safe_filename(filename)
    candidate = (base / name).resolve(strict=False)
    if not _is_within(candidate, base):
        raise PathValidationError(
            f"resolved path escapes the target directory: {candidate!r}"
        )
    return candidate


def _is_within(path: Path, root: Path) -> bool:
    """True if ``path`` is ``root`` or nested under it."""
    try:
        return path == root or path.is_relative_to(root)
    except ValueError:
        return False


# --- SSRF guard -----------------------------------------------------------

def _is_blocked_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        # Unparseable address -> treat as blocked, fail closed.
        return True
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def validate_image_url(url: str) -> str:
    """Validate an outbound image URL against SSRF.

    Enforces an http/https scheme and rejects any URL whose host resolves to a
    private, loopback, link-local, multicast, reserved, or unspecified address
    (IPv4 and IPv6). Returns the URL unchanged on success.
    """
    if not url or not isinstance(url, str):
        raise PathValidationError("image_url must be a non-empty string")

    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise PathValidationError(
            f"image_url must use http or https, got {parts.scheme!r}"
        )

    host = parts.hostname
    if not host:
        raise PathValidationError("image_url has no host")

    # Resolve every address the host maps to; block if ANY is internal so a
    # rebinding/multi-A-record host cannot slip a private IP past us.
    try:
        infos = socket.getaddrinfo(host, parts.port or None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise PathValidationError(f"could not resolve host {host!r}") from exc

    addrs = {info[4][0] for info in infos}
    if not addrs:
        raise PathValidationError(f"host {host!r} resolved to no address")

    for ip in addrs:
        if _is_blocked_ip(ip):
            raise PathValidationError(
                f"image_url host {host!r} resolves to a blocked address ({ip})"
            )

    return url
