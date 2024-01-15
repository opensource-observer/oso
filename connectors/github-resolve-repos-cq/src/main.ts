import { createServeCommand } from "@cloudquery/plugin-sdk-javascript/plugin/serve";

import { newGithubResolveReposPlugin } from "./plugin.js";

const main = () => {
  createServeCommand(newGithubResolveReposPlugin()).parse();
};

main();