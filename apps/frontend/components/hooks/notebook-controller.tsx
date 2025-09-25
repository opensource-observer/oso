"use client";

import { RpcStub, newMessagePortRpcSession } from "capnweb";
import { NotebookControls } from "@/lib/notebook/notebook-controls";
import { useEffect, useState } from "react";
import { logger } from "@/lib/logger";

export function useNotebookController(
  clientId: string,
  iframeRef: React.RefObject<HTMLIFrameElement | null>,
) {
  const [rpcSession, setRpcSession] =
    useState<RpcStub<NotebookControls> | null>(null);

  useEffect(() => {
    // If the ref is not set we can't connect to the iframe
    if (!iframeRef.current) {
      return;
    }
    const iframe = iframeRef.current;

    // Initiate connection to the iframe after the iframe has loaded
    const handleLoad = () => {
      if (!iframe.contentWindow) {
        logger.error("iframe contentWindow is null");
        return;
      }
      // Send a connection request to the iframe to get a MessagePort
      iframe.contentWindow.postMessage({
        command: "requestConnection",
        id: clientId,
      });

      iframe.removeEventListener("load", handleLoad);
    };

    iframe.addEventListener("load", handleLoad);

    const handleConnectionResponse = (event: MessageEvent<any>) => {
      if (event.source !== iframe.contentWindow) {
        return;
      }
      if (!event.data || !event.data.command || !event.data.id) {
        return;
      }

      if (event.data.command === "initialize" && event.data.id === clientId) {
        const port: MessagePort = event.data.port;
        const session = newMessagePortRpcSession<NotebookControls>(port);

        // Once the stub is ready we change the rpcStub state
        setRpcSession(session);
      }
    };
    window.addEventListener("message", handleConnectionResponse);

    return () => {
      iframe.removeEventListener("load", handleLoad);
      window.removeEventListener("message", handleConnectionResponse);
    };
  }, [iframeRef]);

  return rpcSession;
}
