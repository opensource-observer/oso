-- Create a table for the data collective
CREATE TABLE data_collective (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  user_id UUID REFERENCES auth.users NOT NULL,
  name text NOT NULL,
  description text
);

-- Set up Row Level Security (RLS)
-- See https://supabase.com/docs/guides/auth/row-level-security for more details.
ALTER TABLE data_collective
  ENABLE ROW LEVEL SECURITY;

-- No policies means it's not accessible to anyone
