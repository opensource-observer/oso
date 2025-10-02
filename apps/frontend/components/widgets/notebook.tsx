"use client";

import { useEffect, useState } from "react";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import {
  NotebookHostControls,
  NotebookControlsStub,
} from "@/lib/notebook/notebook-controls";
import { ControllableNotebook } from "@/components/widgets/controllable-notebook";
import { NotebookProps } from "@/components/widgets/notebook-meta";
import { logger } from "@/lib/logger";

function Notebook(props: NotebookProps) {
  const {
    className,
    accessToken,
    notebookId,
    initialCode,
    notebookUrl,
    extraEnvironment,
    aiPrompt,
    enableSave,
  } = props;
  const osoAppClient = useOsoAppClient();
  const [_rpcSession, setRpcSession] = useState<NotebookControlsStub | null>(
    null,
  );

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
          throw new Error("No OsoAppClient available, cannot save notebook");
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
          logger.error("No OsoAppClient available, cannot read notebook");
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
    OSO_API_KEY: accessToken,
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

export default Notebook;
