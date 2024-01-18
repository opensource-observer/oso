import { createServeCommand } from "@cloudquery/plugin-sdk-javascript/plugin/serve";

import { newOssDirectoryPlugin } from "./plugin.js";

const main = () => {
  createServeCommand(newOssDirectoryPlugin())
    .parse()
    .catch((err: any) => {
      console.log("caught a plugin error");
      // eslint-disable-next-line no-restricted-properties
      console.error(err);
      process.exit(1);
    });
};

main();
