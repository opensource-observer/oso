import { ApolloWrapper } from "@/components/dataprovider/apollo-wrapper";
import { PostHogProvider } from "@/components/dataprovider/posthog-provider";
import { SupabaseProvider } from "@/components/hooks/supabase";
import { GoogleAnalytics } from "@/components/widgets/google-analytics";
import "@/app/globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/img/oso-emblem-black.svg" />
      </head>
      <body>
        <SupabaseProvider>
          <PostHogProvider>
            <ApolloWrapper>{children}</ApolloWrapper>
          </PostHogProvider>
        </SupabaseProvider>
      </body>
      <GoogleAnalytics />
    </html>
  );
}
