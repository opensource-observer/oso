"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { clientAnalytics } from "../../lib/clients/segment";
import { spawn } from "@opensource-observer/utils";

function Analytics() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    spawn(clientAnalytics!.page());
  }, [pathname, searchParams]);

  return null;
}
export { Analytics };
