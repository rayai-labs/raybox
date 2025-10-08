-- Device authorization flow table (RFC 8628)
CREATE TABLE IF NOT EXISTS device_codes (
    device_code UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_code TEXT NOT NULL UNIQUE,
    verification_uri TEXT NOT NULL DEFAULT 'https://raybox.ai/activate',
    expires_at TIMESTAMPTZ NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    approved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure user_code is uppercase and 6-9 chars (like ABC-123)
    CONSTRAINT user_code_format CHECK (user_code ~ '^[A-Z0-9\-]{6,9}$')
);

-- Index for fast user_code lookups during activation
CREATE INDEX idx_device_codes_user_code ON device_codes(user_code) WHERE approved = false;

-- Index for cleanup of expired codes
CREATE INDEX idx_device_codes_expires_at ON device_codes(expires_at) WHERE approved = false;

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL, -- First 8 chars for display (e.g., "rbx_12345...")
    name TEXT NOT NULL DEFAULT 'CLI',
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ, -- NULL = never expires

    -- Ensure key_hash is bcrypt or SHA-256
    CONSTRAINT key_hash_length CHECK (length(key_hash) >= 32)
);

-- Index for fast API key lookups during authentication
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- Index for user's API keys
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- Function to clean up expired device codes (run periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_device_codes()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM device_codes
    WHERE expires_at < NOW() AND approved = false;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Optional: Set up RLS (Row Level Security) policies
ALTER TABLE device_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own API keys
CREATE POLICY "Users can view own API keys"
    ON api_keys FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can create device codes (no auth required initially)
CREATE POLICY "Anyone can create device codes"
    ON device_codes FOR INSERT
    WITH CHECK (true);

-- Policy: Users can approve their own device codes
CREATE POLICY "Users can approve device codes"
    ON device_codes FOR UPDATE
    USING (auth.uid() = user_id);