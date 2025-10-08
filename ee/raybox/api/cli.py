"""Raybox CLI"""

import subprocess
import sys

from dotenv import load_dotenv


def main():
    """Start Raybox API Server."""
    load_dotenv()

    print("Starting Raybox API Server on http://0.0.0.0:8000")

    try:
        subprocess.run(["serve", "run", "ee.raybox.api.server:raybox_api", "--reload"], check=True)
    except KeyboardInterrupt:
        print("\n✅ Raybox stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
