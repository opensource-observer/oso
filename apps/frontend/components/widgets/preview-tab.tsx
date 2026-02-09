"use client";

import React, { useMemo } from "react";
import useSWR from "swr";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { ColumnDef } from "@tanstack/react-table";
import { AlertCircle, RefreshCw, Download, Copy } from "lucide-react";
import { DataTable } from "@/components/ui/data-table";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ToolTip } from "@/components/ui/tooltip";

import { gql } from "@/lib/graphql/generated";

import { executeGraphQL } from "@/lib/graphql/query";
import { GetPreviewDataQuery } from "@/lib/graphql/generated/graphql";
import { assertNever } from "@opensource-observer/utils";

export interface PreviewData {
  isAvailable: boolean;
  rows: any[];
}

interface PreviewTabProps {
  datasetId: string;
  tableName: string;
  tablePath: string;

  className?: string;

  // Plasmic integration
  useTestData?: boolean;
  testData?: PreviewData;
}

// Unified GraphQL query that handles all model types
const PREVIEW_QUERY = gql(`
  query GetPreviewData($datasetId: ID!, $tableName: String!) {
    datasets(where: { id: { eq: $datasetId } }, single: true) {
      edges {
        node {
          id
          typeDefinition {
            __typename
            ... on DataModelDefinition {
              dataModels(where: { name: { eq: $tableName } }, single: true) {
                edges {
                  node {
                    id
                    name
                    previewData {
                        isAvailable
                        rows
                    }
                  }
                }
              }
            }
            ... on StaticModelDefinition {
              staticModels(where: { name: { eq: $tableName } }, single: true) {
                edges {
                  node {
                    id
                    name
                    previewData {
                      isAvailable
                      rows
                    }
                  }
                }
              }
            }
            ... on DataIngestionDefinition {
              dataIngestion {
                id
                previewData(tableName: $tableName) {
                  isAvailable
                  rows
                }
              }
            }
            ... on DataConnectionDefinition {
              dataConnectionAlias {
                id
                schema
                previewData(tableName: $tableName) {
                  isAvailable
                  rows
                }
              }
            }
          }
        }
      }
    }
  }
`);

function extractPreviewData(
  response: GetPreviewDataQuery,
): PreviewData | undefined {
  const dataset = response?.datasets?.edges?.[0]?.node;
  if (!dataset) return undefined;

  const typeDef = dataset.typeDefinition;

  switch (typeDef?.__typename) {
    case "DataModelDefinition":
      return typeDef?.dataModels?.edges?.[0]?.node?.previewData || undefined;
    case "StaticModelDefinition":
      return typeDef?.staticModels?.edges?.[0]?.node?.previewData || undefined;
    case "DataIngestionDefinition":
      return typeDef?.dataIngestion?.previewData || undefined;
    case "DataConnectionDefinition":
      return typeDef?.dataConnectionAlias?.previewData || undefined;
    default:
      assertNever(typeDef, "Unknown type definition");
  }
}

// Generate columns dynamically from data
function generateColumnsFromData(
  data: PreviewData | undefined,
): ColumnDef<any>[] {
  if (!data || !data.isAvailable || data.rows.length === 0) return [];

  const firstRow = data.rows[0];
  const columnNames = Object.keys(firstRow);

  return columnNames.map((columnName) => ({
    accessorKey: columnName,
    header: columnName,
    cell: ({ getValue }) => {
      const value = getValue();
      if (value == null)
        return <span className="text-muted-foreground">null</span>;
      if (typeof value === "object") return JSON.stringify(value);
      return String(value);
    },
  }));
}

// Custom hook for fetching preview data
function usePreviewData(props: PreviewTabProps) {
  const { datasetId, tableName, useTestData, testData } = props;

  // SWR cache key as array
  const cacheKey = useTestData
    ? null
    : ["/api/v1/osograph/preview", datasetId, tableName];

  const { data, error, isLoading, mutate } = useSWR(
    cacheKey,
    async () => {
      const response = await executeGraphQL(
        PREVIEW_QUERY,
        { datasetId, tableName },
        "Failed to fetch preview data",
      );

      return extractPreviewData(response);
    },
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000,
    },
  );

  return {
    data: useTestData ? testData : data,
    error: useTestData ? null : error,
    isLoading: useTestData ? false : isLoading,
    mutate,
  };
}

function PreviewTab(props: PreviewTabProps) {
  const { className, tablePath } = props;

  const { data: previewData, error, isLoading, mutate } = usePreviewData(props);

  // Generate columns from data
  const columns = useMemo(
    () => generateColumnsFromData(previewData),
    [previewData],
  );

  const noMaterialization = !previewData || !previewData.isAvailable;
  const noData = previewData?.rows.length === 0;

  const handleCopy = () => {
    const columnList = columns.map((col) => col.header).join(",\n");
    void navigator.clipboard.writeText(
      `SELECT ${columnList} FROM ${tablePath} LIMIT 25;`,
    );
  };

  const handleExport = () => {
    if (noData) return;

    const jsonString = JSON.stringify(previewData, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `preview-data.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">Preview data</CardTitle>
        <div className="flex gap-2">
          <ToolTip
            noStyle
            trigger={
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={handleCopy}
                disabled={isLoading || noData}
              >
                <Copy className="h-4 w-4" />
              </Button>
            }
            content={<>Copy</>}
          />
          <ToolTip
            noStyle
            trigger={
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={handleExport}
                disabled={isLoading || noData}
              >
                <Download className="h-4 w-4" />
              </Button>
            }
            content={<>Export as JSON</>}
          />
          <ToolTip
            noStyle
            trigger={
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={() => void mutate()}
                disabled={isLoading}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            }
            content={<>Refresh</>}
          />
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-96 w-full" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center p-8">
            <AlertCircle className="h-8 w-8 text-destructive mb-2" />
            <p className="text-sm text-muted-foreground">
              Failed to load preview data
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {error.message}
            </p>
          </div>
        ) : noMaterialization ? (
          <div className="flex items-center justify-center p-8">
            <p className="text-sm text-muted-foreground">
              No preview data available. Trigger a run to materialize data.
            </p>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={previewData.rows}
            pagination={false}
            defaultPageSize={previewData.rows.length}
          />
        )}
      </CardContent>
    </Card>
  );
}

const PreviewTabMeta: CodeComponentMeta<PreviewTabProps> = {
  name: "PreviewTab",
  description: "Display preview data for models in a card (max 25 rows)",
  props: {
    datasetId: {
      type: "string",
      displayName: "Dataset ID",
      required: true,
    },
    tableName: {
      type: "string",
      displayName: "Table name",
      required: true,
    },
    tablePath: {
      type: "string",
      displayName: "Table path",
      description: "Qualified path to the table",
      required: true,
    },
    useTestData: {
      type: "boolean",
      editOnly: true,
      advanced: true,
      displayName: "Use Test Data",
    },
    testData: {
      type: "array",
      editOnly: true,
      advanced: true,
      displayName: "Test Data",
    },
  },
};

export { PreviewTab, PreviewTabMeta };
