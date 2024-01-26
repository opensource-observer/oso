import type {
  NewClientFunction,
  TableOptions,
  SyncOptions,
  Plugin,
} from "@cloudquery/plugin-sdk-javascript/plugin/plugin";
import {
  newPlugin,
  newUnimplementedDestination,
} from "@cloudquery/plugin-sdk-javascript/plugin/plugin";
import { sync } from "@cloudquery/plugin-sdk-javascript/scheduler";
import type { Table } from "@cloudquery/plugin-sdk-javascript/schema/table";
import { filterTables } from "@cloudquery/plugin-sdk-javascript/schema/table";
import { parseSpec } from "./spec.js";
import type { Spec } from "./spec.js";
import { getTables } from "./tables.js";
import { GraphQLClient } from "graphql-request";
import { Octokit } from "octokit";
import { throttling } from "@octokit/plugin-throttling";

export function graphQLClient(
  token: string,
  graphQLApiUrl: string = "https://api.github.com/graphql",
) {
  return new GraphQLClient(graphQLApiUrl, {
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
}

interface GithubGraphqlClient {
  id(): string;
}

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
    _logger,
    spec,
    { noConnection },
  ) => {
    const parsedSpec = parseSpec(spec);
    pluginClient.spec = parsedSpec;

    const gqlClient = graphQLClient(parsedSpec.token);

    const AppOctoKit = Octokit.plugin(throttling);
    const gh = new AppOctoKit({
      auth: parsedSpec.token,
      throttle: {
        onRateLimit: (retryAfter, options, octokit, retryCount) => {
          const opts = options as {
            method: string;
            url: string;
          };
          octokit.log.warn(
            `Request quota exhausted for request ${opts.method} ${opts.url}`,
          );
          // Retry up to 50 times (that should hopefully be more than enough)
          if (retryCount < 50) {
            octokit.log.info(`Retrying after ${retryAfter} seconds!`);
            return true;
          } else {
            octokit.log.error("failed too many times waiting for github quota");
          }
        },
        onSecondaryRateLimit: (retryAfter, options, octokit, retryCount) => {
          const opts = options as {
            method: string;
            url: string;
          };
          octokit.log.warn(
            `Secondary rate limit detected for ${opts.method} ${opts.url}`,
          );
          if (retryCount < 3) {
            octokit.log.info(`Retrying after ${retryAfter} seconds!`);
            return true;
          } else {
            octokit.log.info(`Failing now`);
          }
        },
      },
    });

    const client: GithubGraphqlClient = {
      id: () => "github-resolve-repos",
    };

    pluginClient.client = client;
    if (noConnection) {
      pluginClient.allTables = [];
      return pluginClient;
    }
    pluginClient.allTables = await getTables(
      parsedSpec.projectsInputPath,
      gqlClient,
      gh,
    );

    return pluginClient;
  };

  pluginClient.plugin = newPlugin("github-resolve-repos", "0.0.1", newClient);
  return pluginClient.plugin;
};
