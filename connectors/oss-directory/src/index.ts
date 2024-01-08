import {
  AirbyteCatalogMessage,
  AirbyteLogger,
  AirbyteSourceBase,
  AirbyteSourceRunner,
  AirbyteSpec,
  AirbyteStreamBase,
} from "faros-airbyte-cdk";
import spec from "./resources/spec.json" assert { type: "json" };
import VError from "verror";

import { Collections, Projects } from "./streams/index.js";
import blockchainAddressSchema from "oss-directory/dist/resources/schema/blockchain-address.json" assert { type: "json" };
import urlSchema from "oss-directory/dist/resources/schema/url.json" assert { type: "json" };
import $RefParser from "@apidevtools/json-schema-ref-parser";
import { FileInfo } from "@apidevtools/json-schema-ref-parser/dist/lib/types";
import path from "path";

const schemaMap: Record<string, Buffer> = {
  "url.json": Buffer.from(JSON.stringify(urlSchema), "utf-8"),
  "blockchain-address.json": Buffer.from(
    JSON.stringify(blockchainAddressSchema),
    "utf-8",
  ),
};

const ossDirectorySchemaResolver = {
  order: 1,
  canRead: new RegExp(`${process.cwd()}/(url|blockchain-address).json`),
  async read(file: FileInfo): Promise<Buffer> {
    const name = path.basename(file.url);
    return schemaMap[name];
  },
};

/** The main entry point. */
export function mainCommand(): Command {
  const logger = new AirbyteLogger();
  const source = new OSSDirectorySource(logger);
  return new AirbyteSourceRunner(logger, source).mainCommand();
}

/** Example source implementation. */
export class OSSDirectorySource extends AirbyteSourceBase<object> {
  async spec(): Promise<AirbyteSpec> {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return new AirbyteSpec(spec);
  }
  async checkConnection(
    _config: object,
  ): Promise<[boolean, VError | undefined]> {
    return [true, undefined];
  }
  streams(): AirbyteStreamBase[] {
    return [new Collections(this.logger), new Projects(this.logger)];
  }

  async discover(config: object): Promise<AirbyteCatalogMessage> {
    const catalog = await super.discover(config);
    for (const stream of catalog.catalog.streams) {
      const streamSchema = stream.json_schema;
      stream.json_schema = await $RefParser.dereference(streamSchema, {
        resolve: { oss: ossDirectorySchemaResolver },
      });
    }
    return catalog;
  }
}

mainCommand().parse();
