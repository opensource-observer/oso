import { createServeCommand } from "@cloudquery/plugin-sdk-javascript/plugin/serve";

import { newOssDirectoryPlugin } from "./plugin.js";

const main = () => {
  // Interestingly this isn't actually a promise but it's not being interpreted correctly
  // eslint-disable-next-line @typescript-eslint/no-floating-promises
  createServeCommand(newOssDirectoryPlugin()).parse();
};

main();
