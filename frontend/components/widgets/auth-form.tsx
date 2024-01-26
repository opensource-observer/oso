"use client";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { supabaseClient } from "../../lib/clients/supabase";

const REDIRECT_URL = "http://localhost:3000/";

type AuthFormProps = {
  className?: string; // Plasmic CSS class
};

export function AuthForm(props: AuthFormProps) {
  const { className } = props;

  return (
    <div className={className}>
      <Auth
        supabaseClient={supabaseClient}
        appearance={{ theme: ThemeSupa }}
        providers={["google"]}
        queryParams={{
          access_type: "offline",
          prompt: "consent",
        }}
        redirectTo={REDIRECT_URL}
        showLinks={false}
        onlyThirdPartyProviders={true}
      />
    </div>
  );
}
