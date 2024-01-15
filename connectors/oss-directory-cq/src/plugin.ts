import type {
  NewClientFunction,
  TableOptions,
  SyncOptions,
  Plugin,
  SourceClient
} from '@cloudquery/plugin-sdk-javascript/plugin/plugin';
import { newPlugin, newUnimplementedDestination } from '@cloudquery/plugin-sdk-javascript/plugin/plugin';
import { sync } from '@cloudquery/plugin-sdk-javascript/scheduler';
import type { Table } from '@cloudquery/plugin-sdk-javascript/schema/table';
import { filterTables } from '@cloudquery/plugin-sdk-javascript/schema/table';
import { parseSpec } from "./spec.js";
import type { Spec } from "./spec.js";
import { getTables } from "./tables.js";

class OssDirectorySourceClient implements SourceClient {
  sync(options: SyncOptions) {

  }

  async tables(options: TableOptions): Promise<Table[]> {
    // Collection and projects tables
    return [];
  }
}


type FileClient = {
  id: () => string;
};

export const newSamplePlugin = () => {
  const pluginClient = {
    ...newUnimplementedDestination(),
    plugin: null as unknown as Plugin,
    spec: null as unknown as Spec,
    client: null as unknown as FileClient | null,
    allTables: null as unknown as Table[],
    close: () => Promise.resolve(),
    tables: ({ tables, skipTables, skipDependentTables }: TableOptions) => {
      const { allTables } = pluginClient;
      const filtered = filterTables(
        allTables,
        tables,
        skipTables,
        skipDependentTables,
      );
      return Promise.resolve(filtered);
    },
    sync: (options: SyncOptions) => {
      const { client, allTables, plugin } = pluginClient;

      if (client === null) {
        return Promise.reject(new Error("Client not initialized"));
      }

      const logger = plugin.getLogger();
      const {
        spec: { concurrency },
      } = pluginClient;

      const {
        stream,
        tables,
        skipTables,
        skipDependentTables,
        deterministicCQId,
      } = options;
      const filtered = filterTables(
        allTables,
        tables,
        skipTables,
        skipDependentTables,
      );

      return sync({
        logger,
        client,
        stream,
        tables: filtered,
        deterministicCQId,
        concurrency,
      });
    },
  };

  const newClient: NewClientFunction = async (
    logger,
    spec,
    { noConnection },
  ) => {
    pluginClient.spec = parseSpec(spec);
    pluginClient.client = { id: () => "oss-directory-noop-client" };
    if (noConnection) {
      pluginClient.allTables = [];
      return pluginClient;
    }
    pluginClient.allTables = await getTables();

    return pluginClient;
  };

  pluginClient.plugin = newPlugin("oss-directory", '0.0.1', newClient);
  return pluginClient.plugin;
};