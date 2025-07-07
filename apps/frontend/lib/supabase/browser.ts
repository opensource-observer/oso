import { createBrowserClient as createSSRBrowserClient } from "@supabase/ssr";
import { Database } from "@/lib/types/supabase";

export function createBrowserClient() {
  return createSSRBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
