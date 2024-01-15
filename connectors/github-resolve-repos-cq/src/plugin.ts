import type {
  NewClientFunction,
  TableOptions,
  SyncOptions,
  Plugin
} from '@cloudquery/plugin-sdk-javascript/plugin/plugin';
import { newPlugin, newUnimplementedDestination } from '@cloudquery/plugin-sdk-javascript/plugin/plugin';
import { sync } from '@cloudquery/plugin-sdk-javascript/scheduler';
import type { Table } from '@cloudquery/plugin-sdk-javascript/schema/table';
import { filterTables } from '@cloudquery/plugin-sdk-javascript/schema/table';
import { parseSpec } from "./spec.js";
import type { Spec } from "./spec.js";
import { getTables } from "./tables.js";
import _ from "lodash";
import { GraphQLClient } from "graphql-request";
import { graphQLClient } from './streams/graphql-client.js';

interface GithubGraphqlClient {
  id(): string;
  client(): GraphQLClient;
};

export const newGithubResolveReposPlugin = () => {
  const pluginClient = {
    ...newUnimplementedDestination(),
    plugin: null as unknown as Plugin,
    spec: null as unknown as Spec,
    client: null as unknown as GithubGraphqlClient | null,
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
    const parsedSpec = parseSpec(spec);
    pluginClient.spec = parsedSpec;


    const gqlClient = graphQLClient(parsedSpec.token);
    const client: GithubGraphqlClient = {
      id: () => 'github-resolve-repos',
      client: () => gqlClient
    }

    pluginClient.client = client;
    if (noConnection) {
      pluginClient.allTables = [];
      return pluginClient;
    }
    pluginClient.allTables = await getTables(parsedSpec.projectsInputPath, gqlClient);

    return pluginClient;
  };

  pluginClient.plugin = newPlugin("github-resolve-repos", '0.0.1', newClient);
  return pluginClient.plugin;
};