import { ApolloWrapper } from "@/components/dataprovider/apollo-wrapper";
import { PostHogProvider } from "@/components/dataprovider/posthog-provider";
import { DebugProvider } from "@/components/dataprovider/debug-provider";
import { SupabaseProvider } from "@/components/hooks/supabase";
import { GoogleAnalytics } from "@/components/widgets/google-analytics";
import { Toaster } from "@/components/ui/sonner";
import { DOMAIN } from "@/lib/config";
import "@/app/globals.css";
import type { Metadata, Viewport } from "next";

const DEFAULT_TITLE = "Open Source Observer";
const DEFAULT_DESCRIPTION =
  "Open Source Observer is a free analytics suite that helps funders " +
  "measure the impact of open source software contributions to the " +
  "health of their ecosystem.";

const PROTOCOL = DOMAIN.includes("localhost") ? "http:" : "https:";
const DEFAULT_OG_IMAGE = new URL(
  "/img/oso-og-banner.png",
  `${PROTOCOL}//${DOMAIN}`,
).toString();

export const viewport: Viewport = {
  themeColor: "#253494",
};

export const metadata: Metadata = {
  title: DEFAULT_TITLE,
  description: DEFAULT_DESCRIPTION,
  openGraph: {
    title: DEFAULT_TITLE,
    description: DEFAULT_DESCRIPTION,
    type: "website",
    images: [
      {
        url: DEFAULT_OG_IMAGE,
        width: 874,
        height: 437,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: DEFAULT_TITLE,
    description: DEFAULT_DESCRIPTION,
    images: [DEFAULT_OG_IMAGE],
  },
};

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
        <Toaster />
        <SupabaseProvider>
          <DebugProvider />
          <PostHogProvider>
            <ApolloWrapper>{children}</ApolloWrapper>
          </PostHogProvider>
        </SupabaseProvider>
      </body>
      <GoogleAnalytics />
    </html>
  );
}
