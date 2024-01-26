"use client";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";
import { Database } from "../../lib/types/supabase";

const REDIRECT_URL = "http://localhost:3000/";

export function AuthForm() {
  const supabase = createClientComponentClient<Database>();

  return (
    <Auth
      supabaseClient={supabase}
      appearance={{ theme: ThemeSupa }}
      view="sign_in"
      providers={["google"]}
      queryParams={{
        access_type: "offline",
        prompt: "consent",
      }}
      redirectTo={REDIRECT_URL}
      showLinks={false}
    />
  );
}
