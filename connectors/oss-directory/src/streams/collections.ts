import { StreamKey, SyncMode } from "faros-airbyte-cdk";
import { Dictionary } from "ts-essentials";
import collectionSchema from "oss-directory/dist/resources/schema/collection.json" assert { type: "json" };
import { OSSDirectoryStreamBase } from "./base.js";

export class Collections extends OSSDirectoryStreamBase {
  getJsonSchema(): Dictionary<any, string> {
    return collectionSchema;
  }

  get primaryKey(): StreamKey {
    return ["slug"];
  }

  async *readRecords(
    _syncMode: SyncMode,
    _cursorField?: string[],
    _streamSlice?: Dictionary<any>,
    _streamState?: Dictionary<any>,
  ): AsyncGenerator<Dictionary<any, string>, any, unknown> {
    const ossDirectoryData = await this.fetchData();
    for (const collection of ossDirectoryData.collections) {
      this.logger.info("hi i am here in a collection");
      this.logger.info(collection.slug);
      yield collection;
    }
  }
}
