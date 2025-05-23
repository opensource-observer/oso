/** @type {import('@babel/core').ConfigFunction} */
module.exports = {
  env: {
    test: {
      plugins: ["@babel/plugin-transform-modules-commonjs"],
    },
  },
};
