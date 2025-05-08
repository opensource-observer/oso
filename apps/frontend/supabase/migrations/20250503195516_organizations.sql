
-- Create a table for organizations
CREATE TABLE organizations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  deleted_at TIMESTAMPTZ,
  user_id UUID REFERENCES auth.users NOT NULL,
  org_name text NOT NULL,

  UNIQUE (org_name),
  CONSTRAINT name_length check (char_length(name) >= 3),
);

-- Many-to-many relationship between organizations and users
CREATE TABLE users_by_organization (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  deleted_at TIMESTAMPTZ,
  user_id UUID REFERENCES auth.users NOT NULL,
  org_id UUID REFERENCES organizations NOT NULL,
  user_role text NOT NULL,

  UNIQUE (user_id, org_id, deleted_at),
);

-- Set up Row Level Security (RLS)
-- See https://supabase.com/docs/guides/auth/row-level-security for more details.
ALTER TABLE organizations
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE users_by_organizations
  ENABLE ROW LEVEL SECURITY;
