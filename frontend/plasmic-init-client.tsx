"use client";

import CircularProgress from "@mui/material/CircularProgress";
import { PlasmicRootProvider } from "@plasmicapp/loader-nextjs";
import { PLASMIC } from "./plasmic-init";
import { ProjectsClientProvider } from "./components/project-browser/project-client-provider";
import { ProjectBrowser } from "./components/project-browser/project-browser";
import { SupabaseQuery } from "./components/dataprovider/supabase-query";
import {
  FormField,
  FormError,
  FormTextField,
  FormSelect,
  FormSlider,
  FormDatePicker,
  FormDropZone,
  FormCheckbox,
} from "./components/forms/form-elements";
import { VisualizationContext } from "./components/forms/visualization-context";

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
  props: {
    variableName: {
      type: "string",
      helpText: "Name to use in Plasmic data picker. Must be unique per query.",
    },

    // SupabaseQueryArgs
    tableName: {
      type: "string",
      helpText: "Supabase table name",
    },
    columns: {
      type: "string",
      helpText: "Comma-separated list of columns",
    },
    filters: {
      type: "object",
      defaultValue: [],
      helpText: "e.g. [['id', 'lt', 10], ['name', 'eq', 'foobar']]",
    },
    limit: {
      type: "number",
      helpText: "Number of rows to return",
    },
    orderBy: {
      type: "string",
      helpText: "Name of column to order by",
    },
    orderAscending: {
      type: "boolean",
      helpText: "True if ascending, false if descending",
    },

    // Plasmic elements
    children: "slot",
    loadingChildren: {
      type: "slot",
      defaultValue: {
        type: "text",
        value: "Placeholder",
      },
    },
    ignoreLoading: {
      type: "boolean",
      helpText: "Don't show 'loadingChildren' even if we're still loading data",
      advanced: true,
    },
    errorChildren: {
      type: "slot",
      defaultValue: {
        type: "text",
        value: "Placeholder",
      },
    },
    ignoreError: {
      type: "boolean",
      helpText: "Don't show 'errorChildren' even if we get an error",
      advanced: true,
    },
    useTestData: {
      type: "boolean",
      helpText: "Render with test data",
      editOnly: true,
      advanced: true,
    },
    testData: {
      type: "object",
      advanced: true,
    },
  },
  providesData: true,
  importPath: "./components/supabase-query",
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
  importPath: "./components/forms",
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
  importPath: "./components/forms",
});

PLASMIC.registerComponent(FormTextField, {
  name: "FormTextField",
  description: "Textfield for forms",
  props: {
    fieldName: {
      type: "string",
      helpText: "Formik field name",
    },
    disabled: "boolean",
    label: "string",
    placeholder: "string",
    multiline: {
      type: "boolean",
      helpText: "Support multiple lines. Automatically resizes the box",
    },
    minRows: {
      type: "number",
      helpText: "If multiline, minimum rows to show",
    },
    maxRows: {
      type: "number",
      helpText: "If multiline, maximum rows to show. Scrolls if more than that",
    },
    rows: {
      type: "number",
      helpText: "If multiline, fixes the number of rows to show",
    },
  },
  importPath: "./components/forms",
});

PLASMIC.registerComponent(FormSelect, {
  name: "FormSelect",
  description: "Select box for forms",
  props: {
    fieldName: {
      type: "string",
      helpText: "Formik field name",
    },
    label: "string",
    optionValues: {
      type: "object",
      defaultValue: ["a", "b"],
    },
    multiple: {
      type: "boolean",
      helpText: "Let the user choose multiple values",
    },
    disabled: "boolean",
  },
  importPath: "./components/forms",
});

PLASMIC.registerComponent(FormSlider, {
  name: "FormSlider",
  description: "Slider for forms",
  props: {
    fieldName: {
      type: "string",
      helpText: "Formik field name",
    },
    disabled: "boolean",
    defaultValue: {
      type: "number",
      helpText: "Starting value",
    },
    min: "number",
    max: "number",
    step: "number",
  },
  importPath: "./components/forms",
});

PLASMIC.registerComponent(FormDatePicker, {
  name: "FormDatePicker",
  description: "Date picker for forms",
  props: {
    fieldName: {
      type: "string",
      helpText: "Formik field name",
    },
    label: "string",
    showUndefined: {
      type: "boolean",
      helpText: "Show checkbox to allow setting to undefined",
    },
    defaultUndefined: "boolean",
    disabled: "boolean",
  },
  importPath: "./components/forms",
});

PLASMIC.registerComponent(FormDropZone, {
  name: "FormDropZone",
  description: "DropZone for forms",
  props: {
    fieldName: {
      type: "string",
      helpText: "Formik field name",
    },
    children: "slot",
    accept: {
      type: "string",
      helpText: "Types of files to accept",
    },
  },
  importPath: "./components/forms",
});

PLASMIC.registerComponent(FormCheckbox, {
  name: "FormCheckbox",
  description: "Checkbox for forms",
  props: {
    fieldName: {
      type: "string",
      helpText: "Formik field name",
    },
  },
  importPath: "./components/forms",
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
  importPath: "./components/hypercert-create",
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
