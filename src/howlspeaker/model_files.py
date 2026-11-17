"""Pinned, bounded model artifacts; no implicit engine downloads or retries."""

import hashlib
import json
import os
import re
import stat
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener


class _Redirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        host = parsed.hostname or ""
        if (parsed.scheme != "https" or parsed.username or parsed.password
                or parsed.port not in (None, 443)
                or not (host == "huggingface.co"
                        or host.endswith(".huggingface.co")
                        or host.endswith(".hf.co"))):
            raise ValueError("Unapproved model download redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch(url, *, timeout):
    return build_opener(_Redirects()).open(url, timeout=timeout)


def load_manifest(path: Path) -> dict:
    if path.stat().st_size > 65536:
        raise ValueError("Manifest is too large")
    value = json.loads(path.read_text())
    _validate(value)
    return value


def _validate(value):
    if not isinstance(value, dict):
        raise ValueError("Invalid model manifest")
    files = value.get("files")
    total = value.get("total_bytes")
    if (value.get("repository") != "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
            or not isinstance(value.get("revision"), str)
            or not re.fullmatch("[a-f0-9]{40}", value["revision"])
            or value.get("license") != "Apache-2.0"
            or type(total) is not int or not 0 < total <= 3 * 1024**3
            or not isinstance(files, list) or not 0 < len(files) <= 32):
        raise ValueError("Invalid model manifest")
    seen = set()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("Invalid artifact")
        name = item.get("path")
        size = item.get("bytes")
        digest = item.get("sha256")
        if (not isinstance(name, str) or len(name) > 200
                or not re.fullmatch(r"[A-Za-z0-9_.\-/]+", name)
                or any(p in ("", ".", "..") for p in name.split("/"))
                or name in seen or type(size) is not int
                or not 0 < size <= 2 * 1024**3
                or not isinstance(digest, str)
                or not re.fullmatch("[a-f0-9]{64}", digest)):
            raise ValueError("Invalid model artifact")
        seen.add(name)
    if sum(item["bytes"] for item in files) != total:
        raise ValueError("Artifact sizes do not match manifest")


def _directory(path):
    """Create private directories via descriptors, refusing symlinks."""
    path = Path(path)
    if ".." in path.parts:
        raise ValueError("Model directory traversal is unsupported")
    fd = os.open(path.anchor or ".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:] if path.anchor else path.parts:
            try:
                os.mkdir(part, 0o700, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def _copy_verified(source, target, item, deadline):
    digest = hashlib.sha256()
    count = 0
    while True:
        if time.monotonic() >= deadline:
            raise ValueError("Model download deadline exceeded")
        data = source.read(min(1024 * 1024, item["bytes"] - count + 1))
        if not data:
            break
        count += len(data)
        if count > item["bytes"]:
            raise ValueError("Model artifact exceeds expected size")
        digest.update(data)
        if target is not None:
            target.write(data)
    if count != item["bytes"] or digest.hexdigest() != item["sha256"]:
        raise ValueError("Model artifact verification failed")


def download_model(manifest: dict, root: Path, *, fetch=_fetch) -> None:
    """Sequential verified publication; external cgroup guard required."""
    _validate(manifest)
    deadline = time.monotonic() + 600
    root_fd = None
    try:
        root_fd = _directory(root)
        for item in manifest["files"]:
            parent = os.dup(root_fd)
            temporary = "." + uuid.uuid4().hex + ".part"
            created = False
            try:
                parts = item["path"].split("/")
                for part in parts[:-1]:
                    try:
                        os.mkdir(part, 0o700, dir_fd=parent)
                    except FileExistsError:
                        pass
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY
                                    | os.O_NOFOLLOW, dir_fd=parent)
                    os.close(parent)
                    parent = child
                try:
                    existing = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW
                                       | os.O_NONBLOCK, dir_fd=parent)
                except FileNotFoundError:
                    existing = None
                if existing is not None:
                    with os.fdopen(existing, "rb") as source:
                        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                            raise ValueError("Cache requires regular files")
                        _copy_verified(source, None, item, deadline)
                    continue
                fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | os.O_NOFOLLOW, 0o600, dir_fd=parent)
                created = True
                url = ("https://huggingface.co/" + manifest["repository"]
                       + "/resolve/" + manifest["revision"] + "/"
                       + item["path"])
                with os.fdopen(fd, "wb") as target:
                    with fetch(url, timeout=30) as source:
                        _copy_verified(source, target, item, deadline)
                    target.flush()
                    os.fsync(target.fileno())
                os.link(temporary, parts[-1], src_dir_fd=parent,
                        dst_dir_fd=parent, follow_symlinks=False)
                os.fsync(parent)
            finally:
                try:
                    if created:
                        os.unlink(temporary, dir_fd=parent)
                finally:
                    os.close(parent)
    except OSError:
        raise ValueError("Model transfer failed; no retries") from None
    finally:
        if root_fd is not None:
            os.close(root_fd)


def verify_model(manifest: dict, root: Path, *, deadline: float) -> None:
    """Offline verification; missing files never trigger downloads."""
    from howlspeaker.export import _open_directory
    _validate(manifest)
    root_fd = None
    try:
        root_fd = _open_directory(root)
        for item in manifest['files']:
            parent = os.dup(root_fd)
            try:
                parts = item['path'].split('/')
                for part in parts[:-1]:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY
                                    | os.O_NOFOLLOW, dir_fd=parent)
                    os.close(parent)
                    parent = child
                fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW
                             | os.O_NONBLOCK, dir_fd=parent)
                with os.fdopen(fd, 'rb') as source:
                    info = os.fstat(source.fileno())
                    if (not stat.S_ISREG(info.st_mode)
                            or info.st_size != item['bytes']):
                        raise ValueError('Invalid cached model artifact')
                    _copy_verified(source, None, item, deadline)
            finally:
                os.close(parent)
    except OSError:
        raise ValueError('Verified local model files are required') from None
    finally:
        if root_fd is not None:
            os.close(root_fd)
