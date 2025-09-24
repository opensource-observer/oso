"use client";

import { useEffect } from "react";
import { OsoAppClient } from "@/lib/clients/oso-app/oso-app";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { logger } from "@/lib/logger";

export function DebugProvider() {
  const { client } = useOsoAppClient();

  useEffect(() => {
    if (process.env.NODE_ENV === "development" && client) {
      window.oso = client;
      logger.log("Debug mode: OsoAppClient available at window.oso");
    }

    return () => {
      if (window.oso) {
        delete window.oso;
      }
    };
  }, [client]);

  return null;
}

declare global {
  interface Window {
    oso?: OsoAppClient;
  }
}
