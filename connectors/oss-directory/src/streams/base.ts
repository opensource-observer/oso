import { AirbyteStreamBase } from "faros-airbyte-cdk";
import { fetchData } from "oss-directory";

export abstract class OSSDirectoryStreamBase extends AirbyteStreamBase {
  protected ossDirectoryData: Awaited<ReturnType<typeof fetchData>>;

  async fetchData() {
    this.logger.warn("about to get oss data");
    if (!this.ossDirectoryData) {
      this.ossDirectoryData = await fetchData();
    }
    return this.ossDirectoryData;
  }
}
