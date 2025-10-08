# Raybox Enterprise Edition (Server)

This directory contains the proprietary Raybox server implementation.

## License

**All code in this directory is proprietary and source-available.**

See [LICENSE](LICENSE) for full terms.

**Summary:**
- ✓ Source code is viewable for transparency and security auditing
- ✗ Production use requires a commercial license
- ✗ Cannot be used to create competing services
- ✗ Cannot be redistributed or modified

## For Licensed Users

If you have a valid Raybox Enterprise license, follow these setup instructions:

### Prerequisites

- Python 3.12+
- Docker
- `brew install sqlc` - Database code generation
- `brew install supabase/tap/supabase` - Database migrations

### Setup

```bash
# Install dependencies
uv sync

# Setup database
cd ee
supabase init
supabase link --project-ref <your-project-ref>
supabase db push

# Generate database types
sqlc generate

# Configure environment
export SUPABASE_DB_URL="postgresql://...pooler.supabase.com:6543/postgres"

# Start server
uv run raybox-server
```

### Development

```bash
# After SQL changes
cd ee && sqlc generate

# After schema changes
cd ee && supabase migration new <name>
cd ee && supabase db push
```

## Getting a License

For production deployment or self-hosting:

- **Email:** enterprise@raybox.ai
- **Website:** https://raybox.ai

## Why Source-Available?

We believe in transparency:
- Review our security practices
- Understand the sandboxing architecture
- Audit code for compliance
- Contribute bug fixes (CLA required)

Production use still requires a license.
