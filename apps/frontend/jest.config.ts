import type { Config } from "jest";

const esModules = ["@opensource-observer/utils", "jose"].join("|");

const config: Config = {
  preset: "ts-jest",
  testEnvironment: "node",
  transform: {
    "^.+\\.js?$": ["babel-jest", { configFile: "./babel.config.testing.js" }],
  },
  transformIgnorePatterns: [`node_modules/(?!.*(?:${esModules}))`],
  moduleNameMapper: {
    "^@/(.*)": "<rootDir>/$1",
  },
};

export default config;
