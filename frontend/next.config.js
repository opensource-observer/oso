// @ts-check

/**
 * @type {import('next').NextConfig}
 **/
const nextConfig = {
  //output: 'export',
  productionBrowserSourceMaps: true,
  experimental: {
    serverComponentsExternalPackages: [
      "typeorm",
      "@opensource-observer/indexer",
    ],
  },
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.plugins = [...config.plugins];
    }

    return config;
  },
  async redirects() {
    return [
      {
        source: "/discord",
        destination: "https://discord.com/invite/NGEJ35aWsq",
        permanent: false,
      },
      {
        source: "/docs",
        destination:
          "https://github.com/opensource-observer/oso/tree/main/docs",
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
};

module.exports = nextConfig;
