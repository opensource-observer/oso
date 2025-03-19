"use client";

import dynamic from "next/dynamic";
import { PlasmicRootProvider } from "@plasmicapp/loader-nextjs";
import { ALGOLIA_INDEX } from "./lib/config";
import { PLASMIC } from "./plasmic-init";
import generateApiKey from "generate-api-key";
import CircularProgress from "@mui/material/CircularProgress";
import { AreaChart } from "@tremor/react";
import {
  MetricsDataProvider,
  MetricsDataProviderRegistration,
} from "./components/dataprovider/metrics-data-provider";
//import { AlgoliaSearchList } from "./components/widgets/algolia";
import { FeedbackWrapper } from "./components/widgets/feedback-farm";
import {
  SupabaseQuery,
  SupabaseQueryRegistration,
} from "./components/dataprovider/supabase-query";
import {
  SupabaseWrite,
  SupabaseWriteRegistration,
} from "./components/widgets/supabase-write";
import { BarList } from "./components/widgets/tremor";
import { AuthForm } from "./components/widgets/auth-form";
import {
  AuthRouter,
  AuthRouterRegistration,
} from "./components/dataprovider/auth-router";
import {
  AuthActions,
  AuthActionsRegistration,
} from "./components/widgets/auth-actions";
import { register as registerMetricsUtils } from "./lib/metrics-utils";

/**
 * Plasmic component registration
 *
 * For more details see:
 * https://docs.plasmic.app/learn/code-components-ref/
 */

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
  importPath: "generate-api-key",
});

registerMetricsUtils(PLASMIC);

PLASMIC.registerComponent(CircularProgress, {
  name: "CircularProgress",
  description: "Circular loading widget",
  props: {},
  importPath: "@mui/material/CircularProgress",
});

PLASMIC.registerComponent(MetricsDataProvider, {
  name: "MetricsDataProvider",
  description: "Data context for metrics",
  props: { ...MetricsDataProviderRegistration },
  providesData: true,
  importPath: "./components/dataprovider/metrics-data-provider",
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

PLASMIC.registerComponent(
  //AlgoliaSearchList,
  dynamic(() => import("./components/widgets/algolia"), { ssr: false }),
  {
    name: "AlgoliaSearchList",
    description: "Algolia-powered search list",
    props: {
      children: "slot",
      indexName: {
        type: "string",
        defaultValue: ALGOLIA_INDEX,
        helpText: "Comma-separated Algolia index names",
      },
      placeholder: "string",
      defaultSearchResults: "object",
    },
    providesData: true,
    importPath: "./components/widgets/algolia",
  },
);

PLASMIC.registerComponent(FeedbackWrapper, {
  name: "FeedbackWrapper",
  description: "Feedback Farm click handler",
  props: {
    children: "slot",
  },
  importPath: "./components/widgets/feedback-farm",
});

PLASMIC.registerComponent(SupabaseQuery, {
  name: "SupabaseQuery",
  props: { ...SupabaseQueryRegistration },
  providesData: true,
  importPath: "./components/dataprovider/supabase-query",
});

PLASMIC.registerComponent(SupabaseWrite, {
  name: "SupabaseWrite",
  props: { ...SupabaseWriteRegistration },
  importPath: "./components/widgets/supabase-write",
});

PLASMIC.registerComponent(AuthForm, {
  name: "AuthForm",
  description: "Supabase Auth Form",
  props: {},
  importPath: "./components/widgets/auth-form",
});

PLASMIC.registerComponent(AuthRouter, {
  name: "AuthRouter",
  props: { ...AuthRouterRegistration },
  providesData: true,
  importPath: "./components/dataprovider/auth-router",
});

PLASMIC.registerComponent(AuthActions, {
  name: "AuthActions",
  description: "Series of authentication-related click handlers",
  props: { ...AuthActionsRegistration },
  importPath: "./components/widgets/auth-actions",
});

/**
PLASMIC.registerComponent(FormField, {
  name: "FormField",
  description: "General purpose form field that accepts an arbitrary input",
  props: {
    fieldName: {
      type: "string",
      helpText: "Formik field name",
    },
    children: "slot",
  },
  importPath: "./components/forms/form-elements",
});

PLASMIC.registerComponent(FormError, {
  name: "FormError",
  description: "Displays the error associated with fieldName",
  props: {
    fieldName: {
      type: "string",
      helpText: "Formik field name",
    },
  },
  importPath: "./components/forms/form-elements",
});

PLASMIC.registerComponent(VisualizationContext, {
  name: "VisualizationContext",
  description: "Context for a group of visualization controls",
  props: {
    variableName: {
      type: "string",
      defaultValue: "vizContext",
      helpText: "Name to use in Plasmic data picker",
    },
    children: {
      type: "slot",
      defaultValue: {
        type: "text",
        value: "Placeholder",
      },
    },
  },
  providesData: true,
  importPath: "./components/forms/visualization-context",
});

PLASMIC.registerComponent(ProjectsClientProvider, {
  name: "ProjectsClientProvider",
  description: "Provides the client for OS Observer",
  props: {
    children: "slot",
    variableName: {
      type: "string",
      defaultValue: "projectsClient",
      helpText: "Name to use in Plasmic data picker",
    },
    useTestData: {
      type: "boolean",
      helpText: "Render with test data",
      editOnly: true,
    },
    testData: "object",
  },
  providesData: true,
  defaultStyles: {
    width: "Full bleed",
  },
});

PLASMIC.registerComponent(ProjectBrowser, {
  name: "ProjectBrowser",
  description: "Project browser",
  props: {},
  importPath: "./components/project-browser",
  defaultStyles: {
    width: "100%",
    minHeight: 300,
  },
});

 */

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
