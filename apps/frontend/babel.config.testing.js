/** @type {import('@babel/core').ConfigFunction} */
module.exports = {
  env: {
    test: {
      plugins: [
        "@babel/plugin-transform-export-namespace-from",
        "@babel/plugin-transform-modules-commonjs",
      ],
    },
  },
};
