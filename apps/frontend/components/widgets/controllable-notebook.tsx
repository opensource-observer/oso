"use client";

import { useEffect, useState } from "react";
import { compressToEncodedURIComponent } from "lz-string";
import { newMessagePortRpcSession } from "capnweb";
import {
  InitializationCommand,
  NotebookControls,
  NotebookControlsStub,
  NotebookHostControls,
} from "@/lib/notebook/notebook-controls";
import { logger } from "@/lib/logger";
import { NotebookHostRpc } from "@/lib/notebook/notebook-host-rpc";

interface ControllableNotebookProps {
  className?: string; // Plasmic CSS class
  initialCode?: string;
  notebookUrl: string;
  environment: Record<string, string>;
  aiPrompt?: string;
  enablePostMessageStore?: boolean;
  onNotebookLoaded: (rpcSession: NotebookControlsStub) => void;
  hostControls: NotebookHostControls;
  enableDebug?: boolean;
}

/**
 * A very generic notebook component that renders a marimo notebook that we can
 * control. This component does not have any supabase or other specific logic so
 * we can easily embed/test this in a storybook or other environment.
 *
 * @param props ControllableNotebookProps
 */
function ControllableNotebook(props: ControllableNotebookProps) {
  const {
    className,
    initialCode,
    notebookUrl,
    environment,
    aiPrompt,
    enablePostMessageStore = true,
    enableDebug = false,
    onNotebookLoaded,
    hostControls: handler,
  } = props;

  const envString = compressToEncodedURIComponent(JSON.stringify(environment));

  // We set a unique id for each instance of the notebook to avoid collisions if
  // there are multiple notebooks rendered at once. This allows us to have
  // multiple independent notebooks on the same page. This is a purely ephemeral
  // value that is not to be persisted in a database, it's purely for the client
  // side.
  const [notebookHostId] = useState<string>(crypto.randomUUID());
  const [hostRpc] = useState<NotebookHostRpc>(new NotebookHostRpc());

  useEffect(() => {
    hostRpc.setHandler(handler);
  }, [handler]);

  const requestConnection = (iframe: HTMLIFrameElement) => {
    const messageChannel = new MessageChannel();
    if (!iframe.contentWindow) {
      return;
    }
    console.log("Requesting connection to notebook iframe");

    newMessagePortRpcSession(messageChannel.port1, hostRpc);

    iframe.contentWindow.postMessage(
      {
        command: "requestConnection",
        id: notebookHostId,
      },
      new URL(notebookUrl).origin,
    );
  };

  const refCallback = (iframe: HTMLIFrameElement | null) => {
    if (!iframe) {
      return;
    }

    let connectionInterval: NodeJS.Timeout | null = null;

    // Initiate connection to the iframe after the iframe has loaded
    const handleLoad = () => {
      // Send a connection request to the iframe to get a MessagePort
      // Keep retrying until we get a response
      connectionInterval = setInterval(() => {
        requestConnection(iframe);
      }, 500);
    };

    iframe.addEventListener("load", handleLoad);

    const handleConnectionResponse = (event: MessageEvent<any>) => {
      if (event.source !== iframe.contentWindow) {
        return;
      }
      if (!event.data || !event.data.command || !event.data.id) {
        return;
      }

      if (event.data.command === "initialize") {
        const command = event.data as InitializationCommand;

        if (!command.recvPort) {
          logger.error("No recvPort provided in initialize command");
          return;
        }
        if (!command.sendPort) {
          logger.error("No sendPort provided in initialize command");
          return;
        }

        const sendPort: MessagePort = command.sendPort;
        const session = newMessagePortRpcSession<NotebookControls>(sendPort);

        // Listen on the recvPort
        newMessagePortRpcSession(command.recvPort, hostRpc);

        // Once the session is ready we notify the parent component
        console.log("Notebook RPC session established");
        console.log(session);
        onNotebookLoaded(session);

        // Stop listening for messages once we've connected
        window.removeEventListener("message", handleConnectionResponse);

        // Stop the connection retry interval
        if (connectionInterval) {
          clearInterval(connectionInterval);
        }
      }
    };
    window.addEventListener("message", handleConnectionResponse);
  };

  // Generate query params
  const queryParams = new URLSearchParams();
  if (aiPrompt) {
    queryParams.append("aiPrompt", aiPrompt);
  }
  if (initialCode) {
    queryParams.append("code", initialCode);
  }
  queryParams.append("env", envString);

  if (enablePostMessageStore) {
    queryParams.append("enablePostMessageStore", "true");
  }
  if (enableDebug) {
    queryParams.append("enableDebug", "true");
  }

  const queryString = queryParams.toString();
  const fullNotebookUrl = `${notebookUrl}#${queryString}`;

  return (
    <iframe
      ref={refCallback}
      className={className}
      src={fullNotebookUrl}
    ></iframe>
  );
}

export { ControllableNotebook, type ControllableNotebookProps };
