"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { spawn } from "@opensource-observer/utils";
import { analytics } from "../../lib/clients/segment";

function Analytics() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    spawn(analytics.page());
  }, [pathname, searchParams]);

  return null;
}
export { Analytics };
