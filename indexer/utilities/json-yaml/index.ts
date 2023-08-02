#!/usr/bin/env node
import fs from "fs";
import YAML from "yaml";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";

type Args = {
  in: string;
  out: string;
};

yargs(hideBin(process.argv))
  .option("in", {
    type: "string",
    describe: "Input file",
  })
  .option("out", {
    type: "string",
    describe: "Output file",
  })
  .command<Args>(
    "json-to-yaml",
    "Converts JSON to YAML",
    (yags) => {
      yags;
    },
    (argv) => {
      const jsonStr = fs.readFileSync(argv.in, "utf8");
      const json = JSON.parse(jsonStr);
      const yaml = YAML.stringify(json);
      fs.writeFileSync(argv.out, yaml);
      console.log(yaml);
    },
  )
  .command<Args>(
    "yaml-to-json",
    "Converts YAML to JSON",
    (yags) => {
      yags;
    },
    (argv) => {
      const yamlStr = fs.readFileSync(argv.in, "utf8");
      const yaml = YAML.parse(yamlStr);
      const json = JSON.stringify(yaml, null, 2);
      fs.writeFileSync(argv.out, json);
      console.log(json);
    },
  )
  .demandCommand()
  .demandOption(["in", "out"])
  .strict()
  .help("h")
  .alias("h", "help")
  .parse();
