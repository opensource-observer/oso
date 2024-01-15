import { StreamKey, SyncMode } from "faros-airbyte-cdk";
import { Dictionary } from "ts-essentials";
import projectSchema from "oss-directory/dist/resources/schema/project.json" assert { type: "json" };
import { OSSDirectoryStreamBase } from "./base.js";

export class Projects extends OSSDirectoryStreamBase {
  getJsonSchema(): Dictionary<any, string> {
    return projectSchema;
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
    for (const project of ossDirectoryData.projects) {
      yield project;
    }
  }
}
