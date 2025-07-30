"use client";

import { Jupyter } from "@datalayer/jupyter-react";
import type { JupyterRootProps } from "@/components/widgets/jupyter-meta";

function JupyterRoot(props: JupyterRootProps) {
  return <Jupyter className={props.className} {...props} />;
}

export default JupyterRoot;
