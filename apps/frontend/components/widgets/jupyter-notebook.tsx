"use client";
import { Notebook } from "@datalayer/jupyter-react";
import type { JupyterNotebookProps } from "@/components/widgets/jupyter-meta";

function JupyterNotebook(props: JupyterNotebookProps) {
  return <Notebook className={props.className} {...props} />;
}

export default JupyterNotebook;
