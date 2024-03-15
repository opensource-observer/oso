--- Creates an auth hook to insert hasura custom claims into JWT tokens
--- See https://supabase.com/docs/guides/auth/auth-hooks?language=add-admin-role#hook-custom-access-token

-- This command is required for local supabase which we use on our github
-- actions. The local supabase doesn't automatically enable the plv8 extension.
create extension if not exists plv8;

create or replace function public.hasura_token_hook(event jsonb)
returns jsonb
language plv8
as $$
  // Check if 'claims.app_metadata' exists in the event object; if not, initialize it
  if (!event.claims) {
    event.claims = {};
  }
  if (!event.claims.app_metadata) {
    event.claims.app_metadata = {};
  }
  // Set Hasura custom claims
  event.claims.app_metadata["x-hasura-default-role"] = 'user';
  event.claims.app_metadata["x-hasura-allowed-roles"] = ['user'];
  event.claims.app_metadata["x-hasura-user-id"] = event.user_id;
  return event;
$$;

grant execute
  on function public.hasura_token_hook
  to supabase_auth_admin;

grant usage on schema public to supabase_auth_admin;

revoke execute
  on function public.hasura_token_hook
  from authenticated, anon;
