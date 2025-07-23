"use client";

import { PlasmicRootProvider } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "@/plasmic-init";
import { format } from "sql-formatter";
import CircularProgress from "@mui/material/CircularProgress";
import { AreaChart } from "@tremor/react";
import { generateApiKey } from "@/lib/auth/keys";
import { BarList } from "@/components/widgets/tremor";
import { registerAllDataProvider } from "@/components/dataprovider";
import { registerAllWidgets } from "@/components/widgets";

/**
 * Plasmic data provider registration
 */
registerAllDataProvider(PLASMIC);

/**
 * Plasmic widgets registration
 */
registerAllWidgets(PLASMIC);

/**
 * Plasmic component registration
 *
 * For more details see:
 * https://docs.plasmic.app/learn/code-components-ref/
 */

PLASMIC.registerFunction(format, {
  name: "formatSql",
  params: [
    {
      name: "query",
      type: "string",
      description: "the SQL query to format",
    },
    {
      name: "options",
      type: "object",
      description: "options to pass to sql-formatter",
    },
  ],
  returnValue: {
    type: "string",
    description: "the formatted SQL",
  },
  importPath: "sql-formatter",
});

PLASMIC.registerFunction(generateApiKey, {
  name: "generateApiKey",
  params: [
    {
      name: "options",
      type: "object",
      description: "See https://www.npmjs.com/package/generate-api-key",
    },
  ],
  returnValue: {
    type: "string",
    description: "the API key",
  },
  importPath: "./lib/auth/keys",
});

PLASMIC.registerComponent(CircularProgress, {
  name: "CircularProgress",
  description: "Circular loading widget",
  props: {},
  importPath: "@mui/material/CircularProgress",
});

PLASMIC.registerComponent(AreaChart, {
  name: "AreaChart",
  description: "Tremor AreaChart",
  props: {
    data: {
      type: "array",
      defaultValue: [],
    },
    categories: {
      type: "array",
    },
    index: {
      type: "string",
      helpText: "Name of the index column",
      defaultValue: "date",
    },
    colors: {
      type: "array",
    },
    startEndOnly: "boolean",
    showXAxis: "boolean",
    showYAxis: "boolean",
    yAxisWidth: "number",
    showAnimation: "boolean",
    animationDuration: "number",
    showTooltip: "boolean",
    showLegend: "boolean",
    showGridLines: "boolean",
    showGradient: "boolean",
    autoMinValue: "boolean",
    minValue: "number",
    maxValue: "number",
    stack: "boolean",
    curveType: {
      type: "choice",
      options: ["linear", "step", "monotone"],
    },
    connectNulls: "boolean",
    allowDecimals: "boolean",
    noDataText: "string",
  },
  importPath: "@tremor/react",
});

PLASMIC.registerComponent(BarList, {
  name: "BarList",
  description: "Tremor BarList",
  props: {
    data: {
      type: "array",
      defaultValue: [],
    },
    colors: {
      type: "array",
      defaultValue: ["blue"],
    },
    showAnimation: "boolean",
  },
  importPath: "./components/widgets/tremor",
});

/**
 * PlasmicClientRootProvider is a Client Component that passes in the loader for you.
 *
 * Why? Props passed from Server to Client Components must be serializable.
 * https://beta.nextjs.org/docs/rendering/server-and-client-components#passing-props-from-server-to-client-components-serialization
 * However, PlasmicRootProvider requires a loader, but the loader is NOT serializable.
 */
export function PlasmicClientRootProvider(
  props: Omit<React.ComponentProps<typeof PlasmicRootProvider>, "loader">,
) {
  return (
    <PlasmicRootProvider loader={PLASMIC} {...props}></PlasmicRootProvider>
  );
}
