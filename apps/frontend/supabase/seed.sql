-- Upsert the test user to avoid errors on re-running the seed
INSERT INTO
    auth.users (
        instance_id,
        id,
        aud,
        role,
        email,
        encrypted_password,
        email_confirmed_at,
        recovery_sent_at,
        last_sign_in_at,
        raw_app_meta_data,
        raw_user_meta_data,
        created_at,
        updated_at,
        confirmation_token,
        email_change,
        email_change_token_new,
        recovery_token
    )
VALUES
    (
        '00000000-0000-0000-0000-000000000000',
        uuid_generate_v4 (),
        'authenticated',
        'authenticated',
        'user@example.com',
        crypt ('password123', gen_salt ('bf')),
        current_timestamp,
        current_timestamp,
        current_timestamp,
        '{"provider":"email","providers":["email"]}',
        '{"name":"Test User"}',
        current_timestamp,
        current_timestamp,
        '',
        '',
        '',
        ''
    );

INSERT INTO organizations (created_by, org_name)
VALUES ((SELECT id FROM auth.users WHERE email = 'user@example.com' LIMIT 1), 'oso');

INSERT INTO notebooks (org_id, created_by, notebook_name, data)
VALUES
    ((SELECT id FROM organizations WHERE org_name = 'oso' LIMIT 1), (SELECT id FROM auth.users WHERE email = 'user@example.com' LIMIT 1), 'template-data-is-beautiful', '{"cells":[{"id":"1","type":"python","content":"print(\"Hello from data-is-beautiful notebook!\")"}]}'),
    ((SELECT id FROM organizations WHERE org_name = 'oso' LIMIT 1), (SELECT id FROM auth.users WHERE email = 'user@example.com' LIMIT 1), 'template-leaderboard', '{"cells":[{"id":"1","type":"python","content":"print(\"Hello from leaderboard notebook!\")"}]}'),
    ((SELECT id FROM organizations WHERE org_name = 'oso' LIMIT 1), (SELECT id FROM auth.users WHERE email = 'user@example.com' LIMIT 1), 'template-value-chain', '{"cells":[{"id":"1","type":"python","content":"print(\"Hello from value-chain notebook!\")"}]}');

INSERT INTO resource_permissions (permission_level, notebook_id) SELECT 'read', id FROM notebooks;

INSERT INTO datasets (org_id, created_by, name, display_name, description, dataset_type)
VALUES
    ((SELECT id FROM organizations WHERE org_name = 'oso' LIMIT 1), (SELECT id FROM auth.users WHERE email = 'user@example.com' LIMIT 1), 'oso-dataset', 'oso-dataset', 'OSO dataset', 'DATA_CONNECTION');