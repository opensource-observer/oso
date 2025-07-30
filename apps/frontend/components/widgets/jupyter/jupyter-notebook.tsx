"use client";
import { Notebook } from "@datalayer/jupyter-react";
import type { JupyterNotebookProps } from "@/components/widgets/jupyter/jupyter-meta";

function JupyterNotebook(props: JupyterNotebookProps) {
  const { className, ...restProps } = props;
  return (
    <div className={className}>
      <Notebook {...restProps} />
    </div>
  );
}

export default JupyterNotebook;
