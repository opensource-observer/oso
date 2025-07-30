"use client";
import { Console } from "@datalayer/jupyter-react";
import type { JupyterConsoleProps } from "@/components/widgets/jupyter-meta";

function JupyterConsole(props: JupyterConsoleProps) {
  return (
    <div className={props.className}>
      <Console />
    </div>
  );
}

export default JupyterConsole;
