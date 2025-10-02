"use client";

import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useEffect, useState } from "react";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import {
  NotebookHostControls,
  NotebookControls,
} from "@/lib/notebook/notebook-controls";
//import { NotebookProps } from "@/components/widgets/notebook-meta";
import { logger } from "@/lib/logger";
import dynamic from "next/dynamic";

export interface NotebookProps {
  className?: string; // Plasmic CSS class
  enableSave: boolean;
  notebookId: string;
  osoApiKey: string;
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
          } = props;
          const osoAppClient = useOsoAppClient();
          const [_rpcSession, setRpcSession] =
            useState<NotebookControls | null>(null);

          const [notebookHostControlsHandler, setNotebookHostControlsHandler] =
            useState<NotebookHostControls>({
              saveNotebook: async (_contents: string) => {},
              readNotebook: async () => {
                return null;
              },
            });

          useEffect(() => {
            setNotebookHostControlsHandler({
              saveNotebook: async (contents: string) => {
                if (!enableSave) {
                  logger.warn("Save is disabled, not saving notebook");
                  return;
                }

                if (!osoAppClient.client) {
                  throw new Error(
                    "No OsoAppClient available, cannot save notebook",
                  );
                }
                if (!notebookId) {
                  throw new Error("Cannot save notebook");
                }

                try {
                  await osoAppClient.client.updateNotebook({
                    id: notebookId,
                    data: contents,
                  });
                  logger.info("Notebook saved successfully");
                } catch (error) {
                  throw new Error("Error saving notebook: " + error);
                }
              },
              readNotebook: async () => {
                if (!osoAppClient.client) {
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
                  const notebook = await osoAppClient.client.getNotebookById({
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
            });
          }, [osoAppClient, notebookId, enableSave]);

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
              onNotebookConnected={(session) => setRpcSession(session)}
              hostControls={notebookHostControlsHandler}
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
