"use client";
import { useEffect, useState } from "react";
import { UserDetails } from "@/lib/types/user";
import { useRouter } from "next/navigation";
import { logger } from "@/lib/logger";
import { useSupabaseState } from "@/components/hooks/supabase";
import { ensure } from "@opensource-observer/utils";

export function useAuth() {
  const [user, setUser] = useState<UserDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const supabaseState = useSupabaseState();
  const supabaseClient = supabaseState?.supabaseClient ?? null;

  useEffect(() => {
    if (!supabaseClient) {
      setLoading(supabaseState?._type === "loading");
      return;
    }

    const fetchUser = async () => {
      try {
        const {
          data: { session },
        } = await supabaseClient.auth.getSession();

        if (session) {
          const { data: userData } = await supabaseClient.auth.getUser();
          if (userData.user) {
            setUser({
              userId: userData.user.id,
              keyName: "login",
              email: userData.user.email,
              name: userData.user.user_metadata?.name || "User",
            });
          }
        }
      } catch (error) {
        logger.error("Error fetching auth user:", error);
      } finally {
        setLoading(false);
      }
    };

    void fetchUser();

    const {
      data: { subscription },
    } = supabaseClient.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setUser({
          userId: session.user.id,
          keyName: "login",
          email: session.user.email,
          name: session.user.user_metadata?.name || "User",
        });
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabaseClient, supabaseState?._type]);

  const signOut = async () => {
    const client = ensure(
      supabaseClient,
      "Supabase client not initialized yet",
    );
    await client.auth.signOut();
    router.push("/");
  };

  return {
    user,
    loading,
    signOut,
    isAuthenticated: !!user,
  };
}
