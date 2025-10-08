-- Device Flow Queries

-- name: CreateDeviceCode :one
INSERT INTO device_codes (
    device_code, user_code, expires_at
) VALUES (
    $1, $2, $3
) RETURNING *;

-- name: GetDeviceCodeByUserCode :one
SELECT * FROM device_codes
WHERE user_code = $1
LIMIT 1;

-- name: GetDeviceCodeByDeviceCode :one
SELECT * FROM device_codes
WHERE device_code = $1
LIMIT 1;

-- name: ApproveDeviceCode :one
UPDATE device_codes
SET approved = true, user_id = $1
WHERE user_code = $2 AND approved = false AND expires_at > NOW()
RETURNING *;

-- API Key Queries

-- name: CreateAPIKey :one
INSERT INTO api_keys (
    user_id, key_hash, key_prefix, name
) VALUES (
    $1, $2, $3, $4
) RETURNING *;

-- name: GetAPIKeyByHash :one
SELECT * FROM api_keys
WHERE key_hash = $1 AND (expires_at IS NULL OR expires_at > NOW())
LIMIT 1;

-- name: UpdateAPIKeyLastUsed :exec
UPDATE api_keys
SET last_used_at = NOW()
WHERE id = $1;

-- name: ListUserAPIKeys :many
SELECT * FROM api_keys
WHERE user_id = $1
ORDER BY created_at DESC;

-- name: DeleteAPIKey :exec
DELETE FROM api_keys
WHERE id = $1 AND user_id = $2;

-- Cleanup Queries

-- name: CleanupExpiredDeviceCodes :exec
DELETE FROM device_codes
WHERE expires_at < NOW() AND approved = false;
