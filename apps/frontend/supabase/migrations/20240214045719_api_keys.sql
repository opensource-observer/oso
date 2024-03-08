-- Create a table for API keys
CREATE TABLE api_keys (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  deleted_at TIMESTAMPTZ,
  user_id UUID REFERENCES auth.users NOT NULL,
  name text NOT NULL,
  api_key text NOT NULL,

  UNIQUE (user_id, name),
  CONSTRAINT name_length check (char_length(name) >= 3),
  CONSTRAINT api_key_length check (char_length(api_key) >= 16)
);

-- Set up Row Level Security (RLS)
-- See https://supabase.com/docs/guides/auth/row-level-security for more details.
ALTER TABLE api_keys 
  ENABLE ROW LEVEL SECURITY;

CREATE POLICY "API Keys are viewable by owner." ON api_keys
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own profile." ON api_keys
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile." ON api_keys
  FOR UPDATE USING (auth.uid() = user_id);

