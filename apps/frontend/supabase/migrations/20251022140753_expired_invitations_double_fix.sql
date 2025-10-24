DROP INDEX IF EXISTS idx_unique_active_invitations;

CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE invitations
ADD CONSTRAINT no_overlapping_invitations
EXCLUDE USING gist (
  LOWER(email) WITH =,
  org_id WITH =,
  tstzrange(created_at, expires_at) WITH &&
)
WHERE (deleted_at IS NULL AND accepted_at IS NULL);
