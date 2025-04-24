"use client";

import Script from "next/script";
import { GOOGLE_ANALYTICS_KEY } from "../../lib/config";

function GoogleAnalytics() {
  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${GOOGLE_ANALYTICS_KEY}`}
      />
      <Script id="google-analytics">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          gtag('config', '${GOOGLE_ANALYTICS_KEY}');
        `}
      </Script>
    </>
  );
}
export { GoogleAnalytics };
