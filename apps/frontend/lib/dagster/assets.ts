import { getDagsterClient } from "@/lib/clients/dagster";
import {
  GET_ASSETS_GRAPH,
  GET_ASSETS_MATERIALIZED_DATA,
} from "@/lib/graphql/dagster_queries";
import { logger } from "@/lib/logger";
import { ApolloClient } from "@apollo/client";

const ASSET_PREFIX = "oso";

type AssetId = string;
type AssetKey = { path: string[] };

interface AssetMaterializationStatus {
  partitionStatus?: {
    numFailed: number;
    numMaterialized: number;
    numMaterializing: number;
    numPartitions: number;
    ranges: {
      endKey: string;
      startKey: string;
      status: string;
    }[];
  };
  latestMaterialization?: number;
}

interface AssetMaterialization {
  key: AssetId;
  status: AssetMaterializationStatus;
  dependencies: AssetId[];
}

function mapAssetKeyToAssetId(assetKey: AssetKey): AssetId {
  return assetKey.path.join(".");
}

function mapAssetIdToAssetKey(key: AssetId): AssetKey {
  return { path: key.split(".") };
}

async function buildAssetGraph(
  client: ApolloClient<any>,
): Promise<Record<string, string[]>> {
  const { data } = await client.query({
    query: GET_ASSETS_GRAPH,
  });
  return data.assetNodes.reduce(
    (acc, node) => {
      const key = mapAssetKeyToAssetId(node.assetKey);
      const dependencies = node.dependencyKeys.map((key) =>
        mapAssetKeyToAssetId(key),
      );
      acc[key] = dependencies;
      return acc;
    },
    {} as Record<string, string[]>,
  );
}

async function getAssetsMaterializedData(
  client: ApolloClient<any>,
  assetKeys: string[],
): Promise<Record<AssetId, AssetMaterializationStatus>> {
  const { data } = await client.query({
    query: GET_ASSETS_MATERIALIZED_DATA,
    variables: {
      assetKeys: assetKeys.map((key) => mapAssetIdToAssetKey(key)),
    },
  });
  return data.assetNodes.reduce(
    (acc, node) => {
      const key = mapAssetKeyToAssetId(node.assetKey);
      const ranges =
        node.assetPartitionStatuses &&
        node.assetPartitionStatuses.__typename === "TimePartitionStatuses"
          ? node.assetPartitionStatuses.ranges
          : [];
      const partitionStatus = node.partitionStats
        ? {
            numFailed: node.partitionStats.numFailed,
            numMaterialized: node.partitionStats.numMaterialized,
            numMaterializing: node.partitionStats.numMaterializing,
            numPartitions: node.partitionStats.numPartitions,
            ranges: ranges.map((range) => ({
              endKey: range.endKey,
              startKey: range.startKey,
              status: range.status,
            })),
          }
        : undefined;
      const latestRun = node.assetMaterializations.length
        ? node.assetMaterializations[0].runOrError
        : undefined;
      const latestMaterialization =
        latestRun?.__typename === "Run"
          ? latestRun.endTime ?? undefined
          : undefined;
      acc[key] = {
        partitionStatus,
        latestMaterialization,
      };
      return acc;
    },
    {} as Record<AssetId, AssetMaterializationStatus>,
  );
}

async function getAssetsMaterializations(
  tables: string[],
): Promise<AssetMaterialization[]> {
  const client = getDagsterClient();
  const graph = await buildAssetGraph(client);

  // Helper function to recursively collect all dependencies
  function collectAllDependencies(
    assetKey: string,
    visited: Set<string> = new Set(),
  ): Set<string> {
    if (visited.has(assetKey)) {
      return visited;
    }

    visited.add(assetKey);

    if (graph[assetKey]) {
      graph[assetKey].forEach((dep) => {
        collectAllDependencies(dep, visited);
      });
    }

    return visited;
  }

  // Collect all asset keys needed (tables + all their dependencies)
  const allAssetKeys = new Set<string>();

  tables.forEach((table) => {
    const tableAssetKey = `${ASSET_PREFIX}.${table}`;
    if (graph[tableAssetKey]) {
      const dependencies = collectAllDependencies(tableAssetKey);
      dependencies.forEach((key) => allAssetKeys.add(key));
    }
  });

  // Get materialization data for all assets
  const statusMap = await getAssetsMaterializedData(
    client,
    Array.from(allAssetKeys),
  );

  // Create a flattened list of AssetMaterialization with dependency references
  const assetMaterializations = new Map<string, AssetMaterialization>();

  // Helper function to add assets with their dependency references
  function addAssetWithDependencies(assetKey: string) {
    if (assetMaterializations.has(assetKey) || !statusMap[assetKey]) {
      return;
    }

    const status = statusMap[assetKey];
    const dependencies = graph[assetKey] || [];

    assetMaterializations.set(assetKey, {
      key: assetKey,
      status,
      dependencies,
    });

    // Recursively add all dependencies
    dependencies.forEach((depKey) => {
      addAssetWithDependencies(depKey);
    });
  }

  // Process each table and its dependencies
  tables.forEach((table) => {
    const tableAssetKey = `${ASSET_PREFIX}.${table}`;
    if (graph[tableAssetKey]) {
      addAssetWithDependencies(tableAssetKey);
    }
  });

  return Array.from(assetMaterializations.values());
}

async function safeGetAssetsMaterializations(
  tables: string[],
): Promise<AssetMaterialization[]> {
  try {
    return await getAssetsMaterializations(tables);
  } catch (error) {
    logger.error(
      `Error fetching asset materialization response for tables ${tables.join(", ")}:`,
      error,
    );
    return [];
  }
}

export { safeGetAssetsMaterializations };

export type { AssetMaterialization };
