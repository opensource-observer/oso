import { createServerClient as createSSRServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { Database } from "@/lib/types/supabase";
import { logger } from "@/lib/logger";

type CookieStore = {
  getAll(): { name: string; value: string }[];
  set(name: string, value: string, options?: Record<string, unknown>): void;
};

const createTestCookieStore = (): CookieStore => ({
  getAll: () => {
    logger.debug("Using test cookie store: returning empty cookies");
    return [];
  },
  set: () => {
    logger.debug("Using test cookie store: setting cookies is a no-op");
  },
});

const getCookieStore = (): CookieStore => {
  if (process.env.NODE_ENV === "test") {
    logger.info("Test environment detected, using test cookie store");
    return createTestCookieStore();
  }

  try {
    return cookies();
  } catch {
    logger.warn("Failed to get cookies, using test cookie store instead");
    return createTestCookieStore();
  }
};

export async function createServerClient() {
  const cookieStore = getCookieStore();

  return createSSRServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // The `setAll` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
      },
    },
  );
}
