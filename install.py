import argparse
import traceback

from ffmpeg_downloader.__main__ import install

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

if __name__ == "__main__":
    from start import main

    print("Installed Successfully, runing bot...")
    main()
