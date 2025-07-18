"use client";

import { redirect } from "next/navigation";
import { useEffect } from "react";
import { logger } from "@/lib/logger";

const REDIRECT_URL = "/retry";

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function Error(props: ErrorPageProps) {
  const { error } = props;
  useEffect(() => {
    logger.error(error);
  }, [error]);

  redirect(REDIRECT_URL);
}
