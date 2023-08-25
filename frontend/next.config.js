// @ts-check
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { PrismaPlugin } = require("@prisma/nextjs-monorepo-workaround-plugin");

/**
 * @type {import('next').NextConfig}
 **/
const nextConfig = {
  //output: 'export',
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.plugins = [...config.plugins, new PrismaPlugin()];
    }

    return config;
  },
};

module.exports = nextConfig;
