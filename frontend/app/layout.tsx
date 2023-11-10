import { ApolloWrapper } from "../components/dataprovider/apollo-wrapper";
import * as snippet from "@segment/snippet";
import { SEGMENT_KEY, NODE_ENV } from "../lib/config";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const renderSnippet = () => {
    const opts = {
      apiKey: SEGMENT_KEY,
      page: true,
    };
    if (NODE_ENV === "development") {
      return snippet.max(opts);
    }
    return snippet.min(opts);
  };
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: renderSnippet() }} />
      </head>
      <body>
        <ApolloWrapper>{children}</ApolloWrapper>
      </body>
    </html>
  );
}
