"use client";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { SupabaseClient } from "@supabase/supabase-js";
import { useSupabaseState } from "@/components/hooks/supabase";

const REDIRECT_URL = "http://localhost:3000/";

type AuthFormProps = {
  className?: string; // Plasmic CSS class
};

const AuthFormMeta: CodeComponentMeta<AuthFormProps> = {
  name: "AuthForm",
  description: "Supabase Auth Form",
  props: {},
  importPath: "./components/widgets/auth-form",
};

function AuthForm(props: AuthFormProps) {
  const { className } = props;
  const supabaseState = useSupabaseState();

  return (
    <div className={className}>
      <Auth
        supabaseClient={supabaseState.supabaseClient as SupabaseClient<any>}
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

export { AuthForm, AuthFormMeta };
