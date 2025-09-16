import os
import subprocess


def ensure_ffmpeg_available() -> bool:
    """Ensure FFmpeg binaries are discoverable by MoviePy and imageio.

    Preference order:
    1) Bundled `ffmpeg-7.1-full_build/bin/ffmpeg(.exe)` in repo root
    2) Any `ffmpeg` already available on PATH

    When a bundled binary exists, sets both `IMAGEIO_FFMPEG_EXE` and
    `FFMPEG_BINARY` and prepends the bin folder to PATH to expose `ffprobe`.
    Returns True if FFmpeg can be invoked, else False.
    """
    try:
        # Compute repo root: this file lives in <repo>/core/ffmpeg_utils.py
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bin_dir = os.path.join(repo_root, "ffmpeg-7.1-full_build", "bin")
        exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        candidate = os.path.join(bin_dir, exe)

        if os.path.exists(candidate):
            # Wire env for both imageio-ffmpeg and MoviePy
            os.environ["IMAGEIO_FFMPEG_EXE"] = candidate
            os.environ["FFMPEG_BINARY"] = candidate
            # Ensure ffprobe is reachable too
            current_path = os.environ.get("PATH", "")
            if bin_dir not in current_path.split(os.pathsep):
                os.environ["PATH"] = f"{bin_dir}{os.pathsep}{current_path}" if current_path else bin_dir

        # Validate availability by calling ffmpeg -version
        with open(os.devnull, "w") as devnull:
            try:
                # Prefer explicit candidate if we set it, else rely on PATH
                cmd = [candidate, "-version"] if os.path.exists(candidate) else ["ffmpeg", "-version"]
                subprocess.check_call(cmd, stdout=devnull, stderr=devnull)
                return True
            except Exception:
                return False
    except Exception:
        return False

