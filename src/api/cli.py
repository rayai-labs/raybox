"""Raybox CLI"""

from dotenv import load_dotenv
import subprocess
import sys


def main():
    """Start Raybox API Server."""
    load_dotenv()

    print("Starting Raybox API Server on http://0.0.0.0:8000")

    try:
        subprocess.run(["serve", "run", "src.api.server:raybox_api", "--reload"], check=True)
    except KeyboardInterrupt:
        print("\n✅ Raybox stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
