"""Unit tests for the server-side input hardening in backend/security.py.

These cover the path-traversal / arbitrary-write guards and the SSRF guard.
DNS resolution in the SSRF tests is monkeypatched so the suite stays offline.
"""

import socket

import pytest

from security import (
    PathValidationError,
    safe_filename,
    safe_output_path,
    validate_dir,
    validate_image_url,
)


# --- safe_filename --------------------------------------------------------

@pytest.mark.parametrize("name", ["image.png", "Bild_01.dds", "a (1).png", "x-y_z.PNG"])
def test_safe_filename_accepts_plain_names(name):
    assert safe_filename(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "../etc/passwd",
        "..\\..\\Windows\\System32\\evil",
        "sub/dir/file.png",
        "sub\\dir\\file.png",
        "/abs/path.png",
        "C:\\abs\\path.png",
        "..",
        ".",
        "",
        "with\x00nul.png",
        "semi;colon.png",
    ],
)
def test_safe_filename_rejects_dangerous_names(name):
    with pytest.raises(PathValidationError):
        safe_filename(name)


# --- validate_dir / safe_output_path --------------------------------------

def test_validate_dir_accepts_existing(tmp_path):
    assert validate_dir(str(tmp_path)) == tmp_path.resolve()


def test_validate_dir_rejects_missing(tmp_path):
    with pytest.raises(PathValidationError):
        validate_dir(str(tmp_path / "does-not-exist"))


def test_validate_dir_rejects_file(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("x")
    with pytest.raises(PathValidationError):
        validate_dir(str(f))


def test_safe_output_path_is_contained(tmp_path):
    out = safe_output_path(str(tmp_path), "pic", ".dds")
    assert out.parent == tmp_path.resolve()
    assert out.name == "pic.dds"


def test_safe_output_path_blocks_traversal_filename(tmp_path):
    with pytest.raises(PathValidationError):
        safe_output_path(str(tmp_path), "../escape", ".png")


def test_allowed_roots_enforced(tmp_path, monkeypatch):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setenv("HAKU_ALLOWED_ROOTS", str(allowed))
    # Inside the allowed root: fine.
    assert validate_dir(str(allowed)) == allowed.resolve()
    # Outside: rejected.
    with pytest.raises(PathValidationError):
        validate_dir(str(outside))


# --- validate_image_url (SSRF) --------------------------------------------

def _fake_getaddrinfo(ip):
    def _inner(host, port, *a, **k):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, port or 0))]
    return _inner


def test_url_rejects_non_http_scheme():
    for url in ["file:///etc/passwd", "ftp://host/x", "gopher://host", "data:text/x,1"]:
        with pytest.raises(PathValidationError):
            validate_image_url(url)


def test_url_allows_public_ip(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    assert validate_image_url("https://example.com/i.png") == "https://example.com/i.png"


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",      # loopback
        "10.0.0.5",       # private /8
        "172.16.0.1",     # private /12
        "192.168.1.10",   # private /16
        "169.254.0.1",    # link-local
        "0.0.0.0",        # unspecified
    ],
)
def test_url_blocks_internal_ipv4(monkeypatch, ip):
    monkeypatch.setattr(socket, "getaddrinfo", _fake_getaddrinfo(ip))
    with pytest.raises(PathValidationError):
        validate_image_url("http://internal.example/i.png")


def test_url_blocks_ipv6_loopback(monkeypatch):
    def _inner(host, port, *a, **k):
        return [(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("::1", port or 0, 0, 0))]
    monkeypatch.setattr(socket, "getaddrinfo", _inner)
    with pytest.raises(PathValidationError):
        validate_image_url("http://ipv6.example/i.png")


def test_url_blocks_when_any_resolved_addr_is_internal(monkeypatch):
    # A host that returns both a public and a private A record must be blocked
    # (defends against DNS-rebinding / mixed records).
    def _inner(host, port, *a, **k):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port or 0)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", port or 0)),
        ]
    monkeypatch.setattr(socket, "getaddrinfo", _inner)
    with pytest.raises(PathValidationError):
        validate_image_url("http://rebind.example/i.png")
