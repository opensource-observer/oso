import { initPlasmicLoader } from "@plasmicapp/loader-nextjs";
import { PLASMIC_PROJECT_ID, PLASMIC_PROJECT_API_TOKEN } from "./lib/config";
import { ProjectsClientProvider } from "./components/project-browser/project-client-provider";
import { ProjectBrowser } from "./components/project-browser/project-browser";

export const PLASMIC = initPlasmicLoader({
  projects: [
    {
      id: PLASMIC_PROJECT_ID,
      token: PLASMIC_PROJECT_API_TOKEN,
    },
  ],
  // Fetches the latest revisions, whether or not they were unpublished!
  // Disable for production to ensure you render only published changes.
  preview: false,
});

/**
 * Plasmic component registration
 *
 * For more details see:
 * https://docs.plasmic.app/learn/code-components-ref/
 */

PLASMIC.registerComponent(ProjectsClientProvider, {
  name: "ProjectsClientProvider",
  description: "Provides the client for OS Observer",
  props: {
    variableName: {
      type: "string",
      defaultValue: "projectsClient",
    },
    children: "slot",
    testData: "object",
    useTestData: {
      type: "boolean",
      helpText: "render with test data",
      editOnly: true,
    },
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
