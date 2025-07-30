"use client";

import { ReactElement } from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import type { JupyterProps, INotebookProps } from "@datalayer/jupyter-react";

type JupyterRootProps = Partial<JupyterProps> & {
  className?: string;
  children?: ReactElement;
};

const JupyterRootMeta: CodeComponentMeta<JupyterRootProps> = {
  name: "JupyterRoot",
  description: "Root wrapper for Jupyter components",
  props: {
    children: "slot",
    jupyterServerUrl: "string",
    jupyterServerToken: "string",
    lite: "boolean",
    terminals: "boolean",
  },
};

type JupyterNotebookProps = Partial<JupyterProps> &
  Partial<INotebookProps> & {
    className?: string;
  };

const JupyterNotebookMeta: CodeComponentMeta<JupyterNotebookProps> = {
  name: "JupyterNotebook",
  description: "Fully-featured Jupyter Notebook component",
  props: {
    ipywidgets: "string",
    nbformat: "object",
    path: "string",
    height: "string",
    maxHeight: "string",
    readonly: "boolean",
  },
};

type JupyterConsoleProps = {
  className?: string;
};

const JupyterConsoleMeta: CodeComponentMeta<JupyterConsoleProps> = {
  name: "JupyterConsole",
  description: "Jupyter Python Console component",
  props: {},
};

export type { JupyterRootProps, JupyterNotebookProps, JupyterConsoleProps };
export { JupyterRootMeta, JupyterNotebookMeta, JupyterConsoleMeta };
