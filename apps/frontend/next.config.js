// @ts-check

/**
 * @type {import('next').NextConfig}
 **/
const nextConfig = {
  ...(process.env.STATIC_EXPORT
    ? {
        // Options for static-export
        output: "export",
      }
    : {
        // Options for non-static-export
        async headers() {
          return [
            {
              // matching all API routes
              source: "/api/:path*",
              //source: "/api/v1/graphql",
              headers: [
                { key: "Access-Control-Allow-Credentials", value: "true" },
                { key: "Access-Control-Allow-Origin", value: "*" }, // replace this your actual origin
                {
                  key: "Access-Control-Allow-Methods",
                  value: "GET,DELETE,PATCH,POST,PUT",
                },
                {
                  key: "Access-Control-Allow-Headers",
                  value:
                    "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization",
                },
              ],
            },
          ];
        },
        async rewrites() {
          return [
            {
              source: "/api/auth",
              destination: "/api/v1/auth",
            },
            {
              source: "/ingest/static/:path*",
              destination: "https://us-assets.i.posthog.com/static/:path*",
            },
            {
              source: "/ingest/:path*",
              destination: "https://us.i.posthog.com/:path*",
            },
            {
              source: "/ingest/decide",
              destination: "https://us.i.posthog.com/decide",
            },
          ];
        },
        async redirects() {
          return [
            {
              source: "/docs/:path*",
              destination: "https://docs.opensource.observer/docs/:path*",
              permanent: true,
            },
            {
              source: "/blog/:path*",
              destination: "https://docs.opensource.observer/blog/:path*",
              permanent: true,
            },
            {
              source: "/assets/:path*",
              destination: "https://docs.opensource.observer/assets/:path*",
              permanent: true,
            },
            {
              source: "/data-collective",
              destination: "https://www.kariba.network",
              permanent: false,
            },
            {
              source: "/discord",
              destination: "https://discord.com/invite/NGEJ35aWsq",
              permanent: false,
            },
            {
              source: "/gather",
              destination:
                "https://app.v2.gather.town/app/c6afa3c8-f374-4fc5-af79-a0a7a45498cb/join?guest=true",
              permanent: false,
            },
            {
              source: "/status",
              destination: "https://status.opensource.observer",
              permanent: false,
            },
            {
              source: "/forms/karibalabs-interest",
              destination: "https://tally.so/r/w7NDv6",
              permanent: false,
            },
            {
              source: "/forms/data-collective-interest",
              destination: "https://tally.so/r/mRD4Pl",
              permanent: false,
            },
          ];
        },
      }),
  productionBrowserSourceMaps: true,
  experimental: {
    serverComponentsExternalPackages: ["typeorm", "graphql"],
  },
  // This is required to support PostHog trailing slash API requests
  skipTrailingSlashRedirect: true,
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.plugins = [...config.plugins];
    }

    return config;
  },
};

module.exports = nextConfig;
