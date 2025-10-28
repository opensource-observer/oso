"use client";

import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useEffect, useState } from "react";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { NotebookHostControls } from "@/lib/notebook/notebook-controls";
import { logger } from "@/lib/logger";
import { saveNotebookPreview } from "@/lib/notebook/utils";
import dynamic from "next/dynamic";

export interface NotebookProps {
  className?: string; // Plasmic CSS class
  enableSave: boolean;
  notebookId: string;
  osoApiKey: string;
  initialCode?: string;
  notebookUrl: string;
  extraEnvironment?: any;
  aiPrompt?: string;
  enableDebug?: boolean;
  mode?: "read" | "edit";
  iframeAllow?: string;
  enablePresentMode?: boolean;
  extraQueryParams?: Record<string, string>;
  extraFragmentParams?: Record<string, string>;
  orgName?: string;
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
    osoApiKey: {
      type: "string",
      displayName: "OSO API Key",
      description: "The API key for the notebook",
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
      required: false,
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
    mode: {
      type: "choice",
      displayName: "Mode",
      description: "The rendering mode for the notebook",
      options: ["read", "edit"],
      defaultValue: "edit",
    },
    enablePresentMode: {
      type: "boolean",
      displayName: "Start the notebook in present mode",
      description: "Whether to start the notebook in present mode",
      defaultValue: false,
    },
    extraFragmentParams: {
      type: "object",
      displayName: "Extra Fragment Params",
      description:
        "Extra fragment parameters to pass to the notebook URL, useful for custom features",
      defaultValue: {},
      required: false,
    },
    extraQueryParams: {
      type: "object",
      displayName: "Extra Query Params",
      description:
        "Extra query parameters to pass to the notebook URL, useful for custom features",
      defaultValue: {},
      required: false,
    },
    iframeAllow: {
      type: "string",
      displayName: "Iframe Allow Options",
      description:
        "The allow options for the iframe, e.g. 'camera; microphone; clipboard-read; clipboard-write'",
      defaultValue: "",
      required: false,
    },
    orgName: {
      type: "string",
      displayName: "Organization Name",
      description:
        "The organization name, used for JWT token generation for GraphQL mutations",
      defaultValue: "",
      required: false,
    },
  },
};

/**
 * We use this factory function to avoid issues with importing capnweb
 * when rendering the build. The build breaks otherwise. So please leave
 * this function here for now until we remove capnweb or fix the build issue.
 */
function NotebookFactory() {
  return dynamic(
    () =>
      import("./controllable-notebook").then((mod) => {
        const ControllableNotebook = mod.ControllableNotebook;
        function Notebook(props: NotebookProps) {
          const {
            className,
            osoApiKey,
            notebookId,
            initialCode,
            notebookUrl,
            extraEnvironment,
            aiPrompt,
            enableSave,
            enableDebug,
            mode = "edit",
            enablePresentMode,
            iframeAllow = "",
            extraFragmentParams = {},
            extraQueryParams = {},
            orgName = "",
          } = props;
          const { client } = useOsoAppClient();
          // Uncomment this if you want to be able to call methods exposed by
          // the notebook
          // const [_rpcSession, setRpcSession] =
          //   useState<NotebookControls | null>(null);

          const [notebookHostControlsHandler, setNotebookHostControlsHandler] =
            useState<NotebookHostControls>({
              saveNotebook: async (_contents: string) => {},
              readNotebook: async () => {
                return null;
              },
              saveNotebookPreview: async (_base64Image: string) => {},
            });

          useEffect(() => {
            setNotebookHostControlsHandler({
              saveNotebook: async (contents: string) => {
                if (!enableSave) {
                  logger.warn("Save is disabled, not saving notebook");
                  return;
                }

                if (!client) {
                  throw new Error(
                    "No OsoAppClient available, cannot save notebook",
                  );
                }
                if (!notebookId) {
                  throw new Error("Cannot save notebook");
                }

                try {
                  await client.updateNotebook({
                    id: notebookId,
                    data: contents,
                  });
                  logger.info("Notebook saved successfully");
                } catch (error) {
                  const errWithMessage = error as { message: string };
                  logger.error("Error saving notebook:", error);
                  if (errWithMessage.message) {
                    if (errWithMessage.message.includes("Failed to fetch")) {
                      throw new Error(
                        "Error saving notebook: disconnected from server",
                      );
                    }
                  }
                  throw new Error("Error saving notebook: " + error);
                }
              },
              readNotebook: async () => {
                if (!client) {
                  logger.error(
                    "No OsoAppClient available, cannot read notebook",
                  );
                  return null;
                }
                if (!notebookId) {
                  logger.error("No notebookId provided, cannot read notebook");
                  return null;
                }
                try {
                  const notebook = await client.getNotebookById({
                    notebookId,
                  });
                  if (!notebook) {
                    logger.warn("No notebook found with id:", notebookId);
                    return null;
                  }
                  logger.info("Notebook read successfully");
                  return notebook.data;
                } catch (error) {
                  logger.error("Error reading notebook:", error);
                  return null;
                }
              },
              saveNotebookPreview: async (base64Image: string) => {
                try {
                  await saveNotebookPreview(notebookId, orgName, base64Image);
                } catch (error) {
                  logger.error("Error saving notebook preview:", error);
                }
              },
            });
          }, [notebookId, enableSave, orgName]);

          // Generate the environment for the notebook
          const environment = {
            OSO_API_KEY: osoApiKey,
            OSO_NOTEBOOK_ID: notebookId,
            ...extraEnvironment,
          };

          return (
            <ControllableNotebook
              className={className}
              initialCode={initialCode}
              notebookUrl={notebookUrl}
              environment={environment}
              notebookId={notebookId}
              aiPrompt={aiPrompt}
              //onNotebookConnected={(session) => setRpcSession(session)}
              hostControls={notebookHostControlsHandler}
              enableDebug={enableDebug}
              mode={mode}
              enablePresentMode={enablePresentMode}
              enablePostMessageStore={enableSave}
              extraFragmentParams={extraFragmentParams}
              extraQueryParams={extraQueryParams}
              iframeAllow={iframeAllow}
            />
          );
        }
        return Notebook;
      }),
    { ssr: false },
  );
}

export { NotebookFactory };

export default NotebookFactory;
