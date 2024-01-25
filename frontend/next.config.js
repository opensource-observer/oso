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
        async rewrites() {
          return [
            {
              source: "/docs/:path*",
              destination: "https://docs.opensource.observer/docs/:path*",
            },
            {
              source: "/blog/:path*",
              destination: "https://docs.opensource.observer/blog/:path*",
            },
            {
              source: "/assets/:path*",
              destination: "https://docs.opensource.observer/assets/:path*",
            },
          ];
        },
        async redirects() {
          return [
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
    serverComponentsExternalPackages: ["typeorm"],
  },
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.plugins = [...config.plugins];
    }

    return config;
  },
};

module.exports = nextConfig;
