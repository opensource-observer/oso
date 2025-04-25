import { ApolloWrapper } from "../components/dataprovider/apollo-wrapper";
import { PostHogProvider } from "../components/dataprovider/posthog-provider";
import { GoogleAnalytics } from "../components/widgets/google-analytics";
import "./globals.css";

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
        <PostHogProvider>
          <ApolloWrapper>{children}</ApolloWrapper>
        </PostHogProvider>
      </body>
      <GoogleAnalytics />
    </html>
  );
}
