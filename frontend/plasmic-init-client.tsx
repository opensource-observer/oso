"use client";

import CircularProgress from "@mui/material/CircularProgress";
import { AreaChart } from "@tremor/react";
import { PlasmicRootProvider } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "./plasmic-init";
import { AlgoliaSearchBox } from "./components/widgets/algolia";
import { FeedbackWrapper } from "./components/widgets/feedback-farm";
import { ProjectsClientProvider } from "./components/project-browser/project-client-provider";
import { ProjectBrowser } from "./components/project-browser/project-browser";
import {
  SupabaseQuery,
  SupabaseQueryRegistration,
} from "./components/dataprovider/supabase-query";
import {
  EventDataProviderRegistration,
  ProjectEventDataProvider,
  ArtifactEventDataProvider,
} from "./components/dataprovider/event-data-provider";
import { FormField, FormError } from "./components/forms/form-elements";
import { VisualizationContext } from "./components/forms/visualization-context";
import { BarList } from "./components/widgets/tremor";

/**
 * Plasmic component registration
 *
 * For more details see:
 * https://docs.plasmic.app/learn/code-components-ref/
 */

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
    color: "string",
    showAnimation: "boolean",
  },
  importPath: "./components/widgets/tremor",
});

PLASMIC.registerComponent(AlgoliaSearchBox, {
  name: "AlgoliaSearchBox",
  description: "Algolia-powered search box",
  props: {},
  importPath: "./components/widgets/algolia",
});

PLASMIC.registerComponent(FeedbackWrapper, {
  name: "FeedbackWrapper",
  description: "Feedback Farm click handler",
  props: {
    children: "slot",
  },
  importPath: "./components/widgets/feedback-farm",
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

PLASMIC.registerComponent(SupabaseQuery, {
  name: "SupabaseQuery",
  props: { ...SupabaseQueryRegistration },
  providesData: true,
  importPath: "./components/dataprovider/supabase-query",
});

PLASMIC.registerComponent(ProjectEventDataProvider, {
  name: "ProjectEventDataProvider",
  props: { ...EventDataProviderRegistration },
  providesData: true,
  importPath: "./components/dataprovider/event-data-provider",
});

PLASMIC.registerComponent(ArtifactEventDataProvider, {
  name: "ArtifactEventDataProvider",
  props: { ...EventDataProviderRegistration },
  providesData: true,
  importPath: "./components/dataprovider/event-data-provider",
});

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
