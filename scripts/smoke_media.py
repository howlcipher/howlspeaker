"""Opt-in synthetic media smoke; no recordings, model downloads or inference.

Run with the installed package: python scripts/smoke_media.py
Requires a working user systemd manager, host python3 and host ffmpeg.
"""

import json
import tempfile
import time
from pathlib import Path

from howlspeaker.export import ExportService
from howlspeaker.media import MediaImporter
from howlspeaker.process import SystemdMediaRunner


def main() -> None:
    results = []
    runner = SystemdMediaRunner()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for kind, options in (
            ("mp3", ["-c:a", "libmp3lame", "-f", "mp3"]),
            ("mp4", ["-c:v", "mpeg4", "-c:a", "aac", "-f", "mp4"]),
        ):
            arguments = ["-hide_banner", "-nostdin", "-loglevel", "error",
                         "-threads", "1", "-filter_threads", "1", "-y"]
            if kind == "mp4":
                arguments += ["-f", "lavfi", "-i", "color=s=64x64:r=1"]
            arguments += ["-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                          "-t", "2", "-threads", "1", *options,
                          "/proc/self/fd/1"]
            with tempfile.TemporaryFile() as empty:
                fixture = runner.convert(empty, arguments,
                                         max_output_bytes=1024**2, timeout=10)
            assert fixture.exit_code == 0 and fixture.output, \
                "Fixture generation failed"
            source = root / ("fixture." + kind)
            source.write_bytes(fixture.output)
            prepared = MediaImporter().prepare(
                path=source, authorized=True,
                provenance="Generated tone fixture",
                start=0.25, seconds=1,
            )
            metadata = ExportService().export_reference(
                prepared.profile, root, kind + ".wav",
            )
            assert 0.9 <= metadata["duration_seconds"] <= 1
            results.append({"case": kind, "status": "PASS",
                            "measurements": prepared.measurements,
                            "audio": metadata})

        # Video without sound must fail without publishing an output.
        with tempfile.TemporaryFile() as empty:
            silent_video = runner.convert(empty, [
                "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i",
                "color=s=64x64:r=1", "-t", "1", "-threads", "1",
                "-c:v", "mpeg4", "-f", "mp4", "/proc/self/fd/1",
            ], max_output_bytes=1024**2, timeout=10)
        assert silent_video.exit_code == 0 and silent_video.output
        source = root / "no_audio.mp4"
        source.write_bytes(silent_video.output)
        try:
            MediaImporter().prepare(path=source, authorized=True,
                                    provenance="Generated video fixture")
        except ValueError:
            results.append({"case": "video_without_audio", "status": "PASS"})
        else:
            raise AssertionError("Video without audio was accepted")

        # Exercise descendant cleanup using only harmless short-lived children.
        child_script = (
            "import subprocess,time; "
            "p=subprocess.Popen(['python3','-c',"
            "'import time;time.sleep(20)']); "
            "print(p.pid,flush=True);time.sleep(20)"
        )
        with tempfile.TemporaryFile() as empty:
            timed = SystemdMediaRunner(ffmpeg="python3").convert(
                empty, ["-c", child_script], max_output_bytes=4096, timeout=1,
            )
        assert timed.exit_code == 124
        pid = int(timed.output.strip())
        for attempt in range(20):
            state_file = Path(f"/proc/{pid}/stat")
            if (not state_file.exists()
                    or state_file.read_text().split()[2] == "Z"):
                break
            time.sleep(0.05)
        else:
            raise AssertionError("Timed-out descendant is still running")
        results.append({"case": "timeout_descendant_cleanup", "status": "PASS",
                        **timed.measurements()})
    print(json.dumps({"real_inference": False, "cases": results}, indent=2))


if __name__ == "__main__":
    main()
