import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

export interface NotebookProps {
  className?: string; // Plasmic CSS class
  enableSave: boolean;
  notebookId: string;
  accessToken: string;
  initialCode?: string;
  notebookUrl: string;
  extraEnvironment: any;
  aiPrompt?: string;
  enableDebug?: boolean;
}

export const NotebookMeta: CodeComponentMeta<NotebookProps> = {
  name: "Notebook",
  description: "OSO's marimo powered notebook",
  props: {
    enableSave: {
      type: "boolean",
      displayName: "Enable Save",
      description:
        "Whether to enable saving the notebook. Set to false for scratch notebooks",
      defaultValue: true,
    },
    notebookId: {
      type: "string",
      displayName: "Notebook ID",
      description: "The ID of the notebook to load",
      defaultValue: "",
    },
    accessToken: {
      type: "string",
      displayName: "Access Token",
      description: "The access token for the notebook",
      defaultValue: "",
    },
    initialCode: {
      type: "string",
      displayName: "Initial Code",
      description: "The initial code to load in the notebook",
      defaultValue: "",
      required: false,
    },
    notebookUrl: {
      type: "string",
      displayName: "Notebook URL",
      description: "The URL of the notebook to load",
    },
    extraEnvironment: {
      type: "object",
      displayName: "Extra Environment",
      description: "Extra environment variables to pass to the notebook",
      defaultValue: {},
    },
    aiPrompt: {
      type: "string",
      displayName: "AI Prompt",
      description:
        "The initial question to ask the AI when Generate With AI is clicked",
      required: false,
    },
    enableDebug: {
      type: "boolean",
      displayName: "Enable Debug",
      description: "Enable debug logging in the notebook iframe",
      defaultValue: false,
    },
  },
};
