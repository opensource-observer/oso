"use client";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { SupabaseClient } from "@supabase/supabase-js";
import { useSupabaseState } from "@/components/hooks/supabase";

const REDIRECT_URL = "http://localhost:3000/";

type AuthFormProps = {
  className?: string; // Plasmic CSS class
};

export function AuthForm(props: AuthFormProps) {
  const { className } = props;
  const supabaseState = useSupabaseState();

  if (!supabaseState) {
    return <>Supabase not initialized yet</>;
  }

  return (
    <div className={className}>
      <Auth
        supabaseClient={supabaseState?.supabaseClient as SupabaseClient<any>}
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
