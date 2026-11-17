import hashlib
import io
import json

import pytest

from howlspeaker.model_files import download_model, load_manifest


def manifest_file(tmp_path, **overrides):
    data = b"known fixture weights"
    values = dict(repository="Qwen/Qwen3-TTS-12Hz-0.6B-Base",
                  revision="a" * 40,
                  license="Apache-2.0", total_bytes=len(data), files=[
                      dict(path="speech_tokenizer/model.safetensors",
                           bytes=len(data),
                           sha256=hashlib.sha256(data).hexdigest()),
                  ])
    values.update(overrides)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(values))
    return path, data


def test_download_hashes_and_reuses_cache(tmp_path):
    path, data = manifest_file(tmp_path)
    calls = []

    def fetch(url, **kwargs):
        calls.append(url)
        return io.BytesIO(data)

    root = tmp_path / "models"
    manifest = load_manifest(path)
    download_model(manifest, root, fetch=fetch)
    artifact = root / "speech_tokenizer/model.safetensors"
    assert artifact.read_bytes() == data
    assert artifact.stat().st_mode & 0o777 == 0o600
    download_model(manifest, root, fetch=fetch)
    assert len(calls) == 1
    assert "a" * 40 in calls[0]
    assert not list(root.rglob("*.part"))


@pytest.mark.parametrize("payload", [b"wrong digest!", b"", b"x" * 100])
def test_corrupt_or_excess_download_not_published(tmp_path, payload):
    path, data = manifest_file(tmp_path)
    root = tmp_path / "models"
    with pytest.raises(ValueError):
        download_model(load_manifest(path), root,
                       fetch=lambda *args, **kwargs: io.BytesIO(payload))
    assert not list(root.rglob("*.safetensors"))
    assert not list(root.rglob("*.part"))


@pytest.mark.parametrize("values", [
    {"revision": "main"}, {"repository": "someone/other-model"},
    {"total_bytes": 0}, {"total_bytes": 4 * 1024**3}, {"files": []},
    {"license": "unknown"},
])
def test_invalid_manifest_rejected(tmp_path, values):
    path, _ = manifest_file(tmp_path, **values)
    with pytest.raises(ValueError):
        load_manifest(path)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "x\\y", "x\nfile"])
def test_manifest_paths_cannot_escape(tmp_path, name):
    path, data = manifest_file(tmp_path)
    values = json.loads(path.read_text())
    values["files"][0]["path"] = name
    path.write_text(json.dumps(values))
    with pytest.raises(ValueError):
        load_manifest(path)


def test_existing_wrong_artifact_unchanged(tmp_path):
    path, data = manifest_file(tmp_path)
    root = tmp_path / "models"
    target = root / "speech_tokenizer/model.safetensors"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"existing file")
    with pytest.raises(ValueError):
        download_model(load_manifest(path), root)
    assert target.read_bytes() == b"existing file"


def test_symlinked_root_rejected_without_writing(tmp_path):
    path, data = manifest_file(tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    root = tmp_path / "models"
    root.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError):
        download_model(load_manifest(path), root,
                       fetch=lambda *args, **kwargs: io.BytesIO(data))
    assert not list(real.iterdir())


def test_nested_directory_symlink_cannot_escape(tmp_path):
    path, data = manifest_file(tmp_path)
    root = tmp_path / "models"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "speech_tokenizer").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        download_model(load_manifest(path), root,
                       fetch=lambda *args, **kwargs: io.BytesIO(data))
    assert not list(outside.iterdir())


def test_interrupted_transfer_cleans_partial(tmp_path):
    path, _ = manifest_file(tmp_path)
    root = tmp_path / "models"

    def fail(*args, **kwargs):
        raise OSError("private network details")

    with pytest.raises(ValueError, match="no retries"):
        download_model(load_manifest(path), root, fetch=fail)
    assert not list(root.rglob("*.part"))
    assert not list(root.rglob("*.safetensors"))


@pytest.mark.parametrize("url", [
    "http://huggingface.co/file", "https://evil.example/file",
    "https://huggingface.co.evil.example/file",
    "https://user@huggingface.co/file", "https://huggingface.co:8443/file",
])
def test_redirect_authority_rejected(url):
    from howlspeaker.model_files import _Redirects
    with pytest.raises(ValueError):
        _Redirects().redirect_request(None, None, 302, "", {}, url)


def test_read_only_model_verification_and_deadline(tmp_path):
    import time
    from howlspeaker.model_files import verify_model
    path, data = manifest_file(tmp_path)
    manifest = load_manifest(path)
    root = tmp_path / 'absent'
    with pytest.raises(ValueError):
        verify_model(manifest, root, deadline=time.monotonic() + 1)
    assert not root.exists()
    download_model(manifest, root,
                   fetch=lambda *args, **kwargs: io.BytesIO(data))
    verify_model(manifest, root, deadline=time.monotonic() + 1)
    with pytest.raises(ValueError, match='deadline'):
        verify_model(manifest, root, deadline=time.monotonic() - 1)
    (root/'speech_tokenizer/model.safetensors').write_bytes(b'x' * len(data))
    with pytest.raises(ValueError):
        verify_model(manifest, root, deadline=time.monotonic() + 1)


def test_read_only_verification_refuses_symlinked_weights(tmp_path):
    import time
    from howlspeaker.model_files import verify_model
    path, data = manifest_file(tmp_path)
    manifest = load_manifest(path)
    root = tmp_path/'models'
    download_model(manifest, root,
                   fetch=lambda *args, **kwargs: io.BytesIO(data))
    weights = root/'speech_tokenizer/model.safetensors'
    outside = tmp_path/'outside'
    weights.rename(outside)
    weights.symlink_to(outside)
    with pytest.raises(ValueError):
        verify_model(manifest, root, deadline=time.monotonic() + 1)
    assert outside.read_bytes() == data
