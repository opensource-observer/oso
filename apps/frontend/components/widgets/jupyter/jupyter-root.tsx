"use client";

import { Jupyter } from "@datalayer/jupyter-react";
import type { JupyterRootProps } from "@/components/widgets/jupyter/jupyter-meta";

function JupyterRoot(props: JupyterRootProps) {
  const { className, children, ...restProps } = props;
  return (
    <div className={className}>
      <Jupyter {...restProps}>{children}</Jupyter>;
    </div>
  );
}

export default JupyterRoot;
