"use client";

import dynamic from "next/dynamic";
import { PlasmicRootProvider } from "@plasmicapp/loader-nextjs";
import { ALGOLIA_INDEX } from "./lib/config";
import { PLASMIC } from "./plasmic-init";
import { format } from "sql-formatter";
import generateApiKey from "generate-api-key";
import CircularProgress from "@mui/material/CircularProgress";
import { AreaChart } from "@tremor/react";
import { Markdown } from "./components/widgets/markdown";
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
import { MonacoEditor } from "./components/widgets/monaco-editor";
import { OSOChat } from "./components/widgets/oso-chat";
import { register as registerMetricsUtils } from "./lib/metrics-utils";
import {
  OsoDataProvider,
  OsoDataProviderRegistration,
} from "./components/dataprovider/oso-data-provider";
import {
  OsoGlobalContext,
  OsoGlobalActions,
  OsoGlobalContextPropsRegistration,
} from "./components/dataprovider/oso-global-context";
import {
  DynamicConnectorForm,
  DynamicConnectorFormRegistration,
} from "./components/widgets/connectors/dynamic-connector-form";
import {
  OsoChatProvider,
  OsoChatProviderRegistration,
} from "./components/dataprovider/oso-chat-provider";

/**
 * Plasmic global context
 */

PLASMIC.registerGlobalContext(OsoGlobalContext, {
  name: "OsoGlobalContext",
  props: { ...OsoGlobalContextPropsRegistration },
  providesData: true,
  globalActions: { ...OsoGlobalActions },
  importPath: "./components/dataprovider/oso-global-context",
});

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
  importPath: "generate-api-key",
});

registerMetricsUtils(PLASMIC);

PLASMIC.registerComponent(CircularProgress, {
  name: "CircularProgress",
  description: "Circular loading widget",
  props: {},
  importPath: "@mui/material/CircularProgress",
});

PLASMIC.registerComponent(Markdown, {
  name: "Markdown",
  description: "Render Markdown",
  props: {
    content: {
      type: "string",
      defaultValue: "Hello World",
      helpText: "Markdown string",
    },
  },
  importPath: "react-markdown",
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

PLASMIC.registerComponent(OSOChat, {
  name: "OSOChat",
  description: "LLM-powered chat overlay",
  props: {
    children: "slot",
  },
  importPath: "./components/widgets/oso-chat",
});

PLASMIC.registerComponent(MonacoEditor, {
  name: "MonacoEditor",
  description: "Monaco editor",
  props: {
    value: {
      type: "string",
    },
    onChange: {
      type: "eventHandler",
      argTypes: [
        {
          name: "value",
          type: "string",
        },
      ],
    },
    height: {
      type: "string",
      defaultValue: "200px",
    },
    language: {
      type: "string",
      defaultValue: "sql",
    },
    theme: {
      type: "string",
      defaultValue: "vs-light",
    },
    options: {
      type: "object",
      defaultValue: {},
    },
  },
  states: {
    value: {
      type: "writable",
      variableType: "text",
      valueProp: "value",
      onChangeProp: "onChange",
    },
  },
  importPath: "./components/widgets/monaco-editor",
});

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

PLASMIC.registerComponent(OsoDataProvider, {
  name: "OsoDataProvider",
  description: "OSO data provider",
  props: { ...OsoDataProviderRegistration },
  providesData: true,
  importPath: "./components/dataprovider/oso-data-provider",
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

PLASMIC.registerComponent(DynamicConnectorForm, {
  name: "DynamicConnectorForm",
  props: {
    ...DynamicConnectorFormRegistration,
  },
  importPath: "./components/widgets/connectors/dynamic-connector-form",
});

PLASMIC.registerComponent(OsoChatProvider, {
  name: "OsoChatProvider",
  props: {
    ...OsoChatProviderRegistration,
  },
  providesData: true,
  importPath: "./components/dataprovider/oso-chat-provider",
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
