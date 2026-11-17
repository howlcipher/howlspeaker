"""Private speaker/take snapshots with explicit selection and no merging."""

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid
from datetime import datetime, timezone

from howlspeaker.config import Configuration
from howlspeaker.export import _open_directory
from howlspeaker.voice import VoiceProfile, validate_snapshot


ID = r'[a-z][a-z0-9_]{0,31}'


def default_store() -> Path:
    base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    if not base.is_absolute():
        raise ValueError('XDG_DATA_HOME must be absolute')
    return base / 'howlspeaker/voices'


def _name(profile_id, take):
    if any(not isinstance(value, str) or not re.fullmatch(ID, value)
           for value in (profile_id, take)):
        raise ValueError('IDs require lowercase letters/digits/underscores')
    return profile_id + '--' + take + '.json'


class ProfileStore:
    def __init__(self, root: Path | None = None,
                 config: Configuration | None = None):
        self.root = Path(root) if root is not None else default_store()
        self.config = config if config is not None else Configuration()

    def _open(self, *, create=False):
        fd = _open_directory(self.root, create=create)
        if os.fstat(fd).st_mode & 0o077:
            os.close(fd)
            raise ValueError('Profile store must be private (mode 700)')
        return fd

    def add(self, profile_id: str, take: str, profile: VoiceProfile,
            *, delivery: str = 'unspecified') -> dict:
        name = _name(profile_id, take)
        if delivery not in ('unspecified', 'natural', 'narration', 'relaxed'):
            raise ValueError('Unsupported delivery label')
        if not isinstance(profile, VoiceProfile):
            raise ValueError('A validated voice profile is required')
        profile = validate_snapshot(
            profile.audio_bytes, authorized=profile.authorized,
            provenance=profile.provenance, transcript=profile.transcript,
            config=self.config,
        )
        record = dict(
            schema=1, profile_id=profile_id, take=take, delivery=delivery,
            created_utc=datetime.now(timezone.utc).isoformat(),
            authorized=True, provenance=profile.provenance,
            transcript=profile.transcript,
            transcript_sha256=hashlib.sha256(
                (profile.transcript or '').encode()).hexdigest(),
            audio_sha256=hashlib.sha256(profile.audio_bytes).hexdigest(),
            audio_base64=base64.b64encode(profile.audio_bytes).decode('ascii'),
        )
        temporary = '.' + uuid.uuid4().hex + '.tmp'
        fd = None
        created = False
        try:
            fd = self._open(create=True)
            target = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            created = True
            with os.fdopen(target, 'w') as stream:
                json.dump(record, stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, name, src_dir_fd=fd, dst_dir_fd=fd,
                    follow_symlinks=False)
            os.fsync(fd)
        except OSError:
            raise ValueError('Cannot save take; existing data preserved') \
                from None
        finally:
            if fd is not None:
                try:
                    if created:
                        os.unlink(temporary, dir_fd=fd)
                finally:
                    os.close(fd)
        return self._metadata(record, profile)

    def _read(self, profile_id, take):
        name = _name(profile_id, take)
        fd = None
        limit = self.config.max_voice_bytes * 4 // 3 + 40000
        try:
            fd = self._open()
            source = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=fd)
            with os.fdopen(source, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077
                        or info.st_size > limit):
                    raise ValueError('Profile file is unsafe or too large')
                data = stream.read(limit + 1)
                if len(data) > limit:
                    raise ValueError('Profile file is too large')
            record = json.loads(data)
            if (type(record['schema']) is not int or record['schema'] != 1
                    or record['profile_id'] != profile_id
                    or record['take'] != take
                    or record['delivery'] not in (
                        'natural', 'narration', 'relaxed', 'unspecified')
                    or not isinstance(record['created_utc'], str)
                    or len(record['created_utc']) > 64):
                raise ValueError('Profile metadata is invalid')
            audio = base64.b64decode(record['audio_base64'], validate=True)
            profile = validate_snapshot(
                audio, authorized=record['authorized'],
                provenance=record['provenance'],
                transcript=record['transcript'],
                config=self.config,
            )
            if (hashlib.sha256(audio).hexdigest() != record['audio_sha256']
                    or hashlib.sha256((profile.transcript or '').encode())
                    .hexdigest() != record['transcript_sha256']):
                raise ValueError('Profile checksum mismatch')
            return record, profile
        except (OSError, KeyError, TypeError, ValueError, binascii.Error,
                RecursionError):
            raise ValueError('Cannot load a valid private profile take') \
                from None
        finally:
            if fd is not None:
                os.close(fd)

    def load(self, profile_id: str, take: str) -> VoiceProfile:
        return self._read(profile_id, take)[1]

    def describe(self, profile_id: str, take: str) -> dict:
        return self._metadata(*self._read(profile_id, take))

    @staticmethod
    def _metadata(record, profile):
        fields = ('profile_id', 'take', 'delivery', 'created_utc',
                  'audio_sha256', 'transcript_sha256')
        return {key: record[key] for key in fields} | profile.audio_metadata()

    def list(self) -> list[dict]:
        fd = None
        try:
            if not self.root.exists():
                return []
            fd = self._open()
            result = []
            with os.scandir(fd) as entries:
                for index, entry in enumerate(entries):
                    if index >= 256:
                        raise ValueError('Store exceeds 256 entries')
                    match = re.fullmatch(f'({ID})--({ID})\\.json', entry.name)
                    if match and entry.is_file(follow_symlinks=False):
                        result.append(dict(profile_id=match[1], take=match[2]))
            return sorted(
                result, key=lambda item: (item['profile_id'], item['take']),
            )
        except OSError:
            raise ValueError('Cannot list private profile store') from None
        finally:
            if fd is not None:
                os.close(fd)

    def delete(self, profile_id: str, take: str) -> None:
        name = _name(profile_id, take)
        fd = None
        try:
            fd = self._open()
            os.unlink(name, dir_fd=fd)
            os.fsync(fd)
        except OSError:
            raise ValueError('Cannot delete profile take') from None
        finally:
            if fd is not None:
                os.close(fd)
