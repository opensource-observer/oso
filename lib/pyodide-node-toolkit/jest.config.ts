import type { Config } from 'jest';
import { TS_EXT_TO_TREAT_AS_ESM, ESM_TS_TRANSFORM_PATTERN } from 'ts-jest'

// const config: Config = {
//   preset: 'ts-jest/presets/default-esm',
//   testEnvironment: 'node',
//   testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)'],
//   transform: {
//     '^.+\\.tsx?$': [
//       'ts-jest',
//       {
//         useESM: true,
//       },
//     ],
//   },
//   moduleFileExtensions: ["js", "jsx", "ts", "tsx"],
//   moduleDirectories: ["node_modules", "src"],
//   //moduleNameMapper: {
//     //'^(\\.{1,2}/.*)\\.js$': '$1',
//   //},
// };
// export default config;

export default {
  extensionsToTreatAsEsm: [...TS_EXT_TO_TREAT_AS_ESM],
  transform: {
    [ESM_TS_TRANSFORM_PATTERN]: [
      'ts-jest',
      {
        //...other `ts-jest` options
        useESM: true,
      },
    ],
  },
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  moduleFileExtensions: ["js", "jsx", "ts", "tsx"],
  moduleDirectories: ["node_modules", "src"],
  testEnvironment: "node",
  preset: "ts-jest/presets/default-esm",
} satisfies Config
