"""Raybox CLI for authentication and management."""

import sys
import webbrowser

from raybox.sdk.python.config import RayboxConfig


def login(api_url: str | None = None) -> None:
    """Authenticate with Raybox and save API key.

    Args:
        api_url: Optional custom API URL (defaults to https://api.raybox.ai)
    """
    config = RayboxConfig()
    base_url = api_url or "https://raybox.ai"

    print("🔐 Authenticating with Raybox...")
    print(f"\nOpening browser to: {base_url}/login")
    print("\nAfter authenticating, you'll receive an API key.")

    # Open browser for authentication
    try:
        webbrowser.open(f"{base_url}/login")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"\nPlease manually visit: {base_url}/login")

    print("\n" + "=" * 60)
    api_key = input("Paste your API key here: ").strip()

    if not api_key:
        print("❌ No API key provided. Authentication cancelled.")
        sys.exit(1)

    # Save the API key
    api_endpoint = api_url or "https://api.raybox.ai"
    config.save_api_key(api_key, api_endpoint)

    print("\n✅ Successfully authenticated!")
    print(f"📍 API URL: {api_endpoint}")
    print(f"💾 Config saved to: {config.config_file}")


def logout() -> None:
    """Clear stored Raybox credentials."""
    config = RayboxConfig()

    if not config.config_file.exists():
        print("ℹ️  No credentials found. Already logged out.")
        return

    config.clear()
    print("✅ Successfully logged out. Credentials cleared.")


def whoami() -> None:
    """Display current authentication status."""
    config = RayboxConfig()
    api_key = config.get_api_key()

    if not api_key:
        print("❌ Not authenticated. Run 'raybox login' to authenticate.")
        sys.exit(1)

    api_url = config.get_api_url()
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"

    print("✅ Authenticated")
    print(f"📍 API URL: {api_url}")
    print(f"🔑 API Key: {masked_key}")


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Raybox CLI - Manage authentication and sandboxes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Authenticate with Raybox")
    login_parser.add_argument(
        "--api-url",
        help="Custom API URL (default: https://api.raybox.ai)",
        default=None,
    )

    # Logout command
    subparsers.add_parser("logout", help="Clear stored credentials")

    # Whoami command
    subparsers.add_parser("whoami", help="Display current authentication status")

    args = parser.parse_args()

    if args.command == "login":
        login(args.api_url)
    elif args.command == "logout":
        logout()
    elif args.command == "whoami":
        whoami()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
