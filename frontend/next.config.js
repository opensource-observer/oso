// @ts-check

/**
 * @type {import('next').NextConfig}
 **/
const nextConfig = {
  //output: 'export',
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
