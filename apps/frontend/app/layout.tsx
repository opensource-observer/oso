import { ApolloWrapper } from "../components/dataprovider/apollo-wrapper";
import { Analytics } from "../components/widgets/analytics";
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
        <ApolloWrapper>{children}</ApolloWrapper>
      </body>
      <Analytics />
    </html>
  );
}
