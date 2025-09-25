"use client";

import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useEffect, useRef, useState } from "react";
import { useSupabaseState } from "@/components/hooks/supabase";
import { compressToEncodedURIComponent } from "lz-string";
import { SupabaseClient } from "@supabase/supabase-js";
import { useNotebookController } from "@/components/hooks/notebook-controller";
import { logger } from "@/lib/logger";

interface NotebookProps {
  className?: string; // Plasmic CSS class
  enableSave: boolean;
  accessToken: string;
  notebookId: string;
  initialCode: string;
  notebookUrl: string;
  extraEnvironment: Record<string, string>;
  aiPrompt?: string;
}

const NotebookMeta: CodeComponentMeta<NotebookProps> = {
  name: "Notebook",
  description: "marimo powered notebook",
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
    },
    accessToken: {
      type: "string",
      displayName: "Access Token",
      description: "The access token for the notebook",
    },
    initialCode: {
      type: "string",
      displayName: "Initial Code",
      description: "The initial code to load in the notebook",
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
    },
  },
};

async function notebookSaveFile(options: {
  notebookId: string;
  supabaseClient: SupabaseClient;
  contents: string;
}) {
  const { notebookId, supabaseClient, contents } = options;

  const { error } = await supabaseClient.from("notebooks").update({
    id: notebookId,
    data: contents,
    updated_at: new Date().toISOString(),
  });
  if (error) {
    throw error;
  }
}

async function notebookReadFile(options: {
  notebookId: string;
  supabaseClient: SupabaseClient;
}) {
  const { notebookId, supabaseClient } = options;

  const { data, error } = await supabaseClient
    .from("notebooks")
    .select("data")
    .eq("id", notebookId)
    .single();
  if (error) {
    throw error;
  }
  return data?.data || "";
}

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
  const supabaseState = useSupabaseState();
  const { supabaseClient } = supabaseState;
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // We set a unique id for each instance of the notebook to avoid collisions if
  // there are multiple notebooks rendered at once. This allows us to have
  // multiple independent notebooks on the same page. This is a purely ephemeral
  // value that is not to be persisted in a database, it's purely for the client
  // side.
  const [notebookHostId] = useState<string>(crypto.randomUUID());

  const rpcSession = useNotebookController(notebookHostId, iframeRef);

  // Register the filestore with the notebook once the rpc is ready. At this
  // time, the oso notebook is set to block until the filestore is registered.
  useEffect(() => {
    if (!rpcSession) {
      return;
    }

    if (!supabaseClient) {
      console.warn(
        "Supabase client not initialized, cannot register filestore",
      );
      return;
    }

    // We register the filestore as a set of callbacks via capnweb
    rpcSession
      .registerNotebookFilestore({
        saveNotebook: async (contents) => {
          if (!enableSave) {
            return;
          }

          await notebookSaveFile({
            notebookId,
            supabaseClient,
            contents,
          });
        },
        readNotebook: async () => {
          return await notebookReadFile({
            notebookId,
            supabaseClient,
          });
        },
      })
      .catch((err) => {
        logger.error(`Error occured registering notebook filestore: ${err}`);
      });
  }, [rpcSession, supabaseClient, notebookId, enableSave]);

  // Generate the environment for the notebook
  const environment = {
    OSO_API_KEY: accessToken,
    OSO_NOTEBOOK_ID: notebookId,
    ...extraEnvironment,
  };
  const envString = compressToEncodedURIComponent(JSON.stringify(environment));

  // Generate query params
  const queryParams = new URLSearchParams();
  if (aiPrompt) {
    queryParams.append("aiPrompt", aiPrompt);
  }
  if (initialCode) {
    queryParams.append("", initialCode);
  }
  queryParams.append("env", envString);

  const queryString = queryParams.toString();
  const fullNotebookUrl = `${notebookUrl}#${queryString}`;

  return (
    <iframe
      ref={iframeRef}
      className={className}
      src={fullNotebookUrl}
    ></iframe>
  );
}

export { Notebook, NotebookMeta };
