
-- Create a table for organizations
CREATE TABLE organizations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_by uuid references auth.users not null,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  deleted_at TIMESTAMPTZ,
  org_name text NOT NULL,

  UNIQUE (org_name),
  CONSTRAINT name_length check (char_length(org_name) >= 3)
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

  UNIQUE (user_id, org_id, deleted_at)
);

-- Set up Row Level Security (RLS)
-- See https://supabase.com/docs/guides/auth/row-level-security for more details.
ALTER TABLE organizations
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE users_by_organization
  ENABLE ROW LEVEL SECURITY;

CREATE policy "Organizations are viewable by public." ON organizations
  AS PERMISSIVE
  FOR SELECT USING (true);

CREATE policy "Any user can create an organization." ON organizations
  AS PERMISSIVE
  FOR INSERT WITH CHECK (
    auth.uid() = organizations.created_by
  );

CREATE policy "Only admins can update organizations." ON organizations
  AS PERMISSIVE
  FOR UPDATE USING (
    -- If I'm the owner/creator
    auth.uid() = organizations.created_by OR
    -- If I'm an admin
    EXISTS (
      SELECT 1
      FROM users_by_organization
      WHERE users_by_organization.user_id = auth.uid()
        AND users_by_organization.org_id = organizations.id
        AND users_by_organization.user_role = 'admin'
        AND users_by_organization.deleted_at IS NULL
    )
  );

CREATE policy "Organizations are viewable by public." ON users_by_organization
  AS PERMISSIVE
  FOR SELECT USING (true);

create policy "Only admins can add members." on users_by_organization
  as PERMISSIVE
  for insert with check (
    -- Any organizations where I'm the owner/creator
    EXISTS (
      SELECT 1
      FROM organizations
      WHERE organizations.id = users_by_organization.org_id
        AND organizations.created_by = auth.uid()
    ) OR
    -- Any organizations where I'm an admin
    EXISTS (
      SELECT 1
      FROM users_by_organization AS u
      WHERE u.user_id = auth.uid()
        AND u.org_id = users_by_organization.id
        AND u.user_role = 'admin'
        AND u.deleted_at IS NULL
    )
  );


CREATE policy "Only admins can update organizations." ON users_by_organization
  AS PERMISSIVE
  for update using (
    -- Any organizations where I'm the owner/creator
    EXISTS (
      SELECT 1
      FROM organizations
      WHERE organizations.id = users_by_organization.org_id
        AND organizations.created_by = auth.uid()
    ) OR
    -- Any organizations where I'm an admin
    EXISTS (
      SELECT 1
      FROM users_by_organization AS u
      WHERE u.user_id = auth.uid()
        AND u.org_id = users_by_organization.id
        AND u.user_role = 'admin'
        AND u.deleted_at IS NULL
    )
  );