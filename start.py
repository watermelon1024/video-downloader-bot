"""
Start the application.
"""

import tracemalloc

tracemalloc.start(25)  # Used in src/client/client.py on_ready function.


def main():
    from decouple import config

    from src.main import Bot

    Bot(config("log-webhook")).run(config("token"))


if __name__ == "__main__":
    main()
