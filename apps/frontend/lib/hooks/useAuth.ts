"use client";
import { useEffect, useState } from "react";
import { createNormalSupabaseClient } from "@/lib/clients/supabase";
import { User } from "@/lib/types/user";
import { useRouter } from "next/navigation";
import { logger } from "@/lib/logger";

const supabaseClient = createNormalSupabaseClient();

export function useAuth() {
  const [user, setUser] = useState<User>({
    role: "anonymous",
    host: null,
  });
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
              role: "user",
              userId: userData.user.id,
              email: userData.user.email,
              name: userData.user.user_metadata?.name || "User",
              keyName: "login",
              host: window.location.hostname,
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
          role: "user",
          userId: session.user.id,
          email: session.user.email,
          name: session.user.user_metadata?.name || "User",
          keyName: "login",
          host: window.location.hostname,
        });
      } else {
        setUser({
          role: "anonymous",
          host: window.location.hostname,
        });
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
    isAuthenticated: user.role !== "anonymous",
  };
}
