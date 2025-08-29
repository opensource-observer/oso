"use client";
import { useEffect, useState } from "react";
import { createBrowserClient } from "@/lib/supabase/browser";
import { UserDetails } from "@/lib/types/user";
import { useRouter } from "next/navigation";
import { logger } from "@/lib/logger";

const supabaseClient = createBrowserClient();

export function useAuth() {
  const [user, setUser] = useState<UserDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
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
  }, []);

  const signOut = async () => {
    await supabaseClient.auth.signOut();
    router.push("/");
  };

  return {
    user,
    loading,
    signOut,
    isAuthenticated: !!user,
  };
}
