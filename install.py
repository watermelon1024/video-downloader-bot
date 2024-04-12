import argparse
import os
import shutil
import traceback

from ffmpeg_downloader.__main__ import install

from src.client.config import Config
from start import main as start


def check_ffmpeg():
    return shutil.which("ffmpeg")


def install_ffmpeg():
    try:
        install(
            argparse.Namespace(
                proxy=None,
                retries=5,
                timeout=15,
                no_cache_dir=False,
                force=False,
                upgrade=True,
                y=True,
                add_path=False,
                no_simlinks=False,
                set_env=None,
                reset_env=False,
                presets=None,
                version=None,
                func=install,
            )
        )
    except Exception:
        print("Error installing ffmpeg...")
        traceback.print_exc()
        exit(1)


def main():
    print("Checking ffmpeg...")
    if check_ffmpeg() or os.access(Config()["ffmpeg"]["path"], os.X_OK):
        print("ffmpeg is already installed, starting the bot...")
        start()
        return

    print("ffmpeg is not installed, installing ffmpeg...")
    install_ffmpeg()
    print("Installed Successfully, starting the bot...")
    start()


if __name__ == "__main__":
    main()
