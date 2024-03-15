#!/bin/bash
set -euo pipefail

cd "$1"

pnpm supabase start
export $(supabase status -o env | xargs)
echo "SUPABASE_SERVICE_KEY=$SERVICE_ROLE_KEY" >> $GITHUB_ENV
echo "SUPABASE_JWT_SECRET=$JWT_SECRET" >> $GITHUB_ENV 
echo "NEXT_PUBLIC_SUPABASE_URL=$API_URL" >> $GITHUB_ENV
echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=$ANON_KEY" >> $GITHUB_ENV
