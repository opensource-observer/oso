-- Add a `queued` status to the run_status enum to represent runs that are
-- waiting in the queue to be processed.
ALTER TYPE run_status ADD VALUE IF NOT EXISTS 'queued';