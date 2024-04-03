"use client";

import { useEffect } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { analytics } from "../../lib/clients/segment";
import { spawn } from "../../lib/common";

function Analytics() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    spawn(analytics.page());
  }, [pathname, searchParams]);

  return null;
}
export { Analytics };
