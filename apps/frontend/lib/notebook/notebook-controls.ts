export interface NotebookPostMessageFilestore {
  // Save the contents of a notebook via the host
  saveNotebook: (contents: string) => Promise<void>;
  // Read the contents of a notebook via the host
  readNotebook: () => Promise<string | null>;
}

export interface NotebookControls {
  createCell: (code: string) => void;

  triggerAlert: (message: string) => void;

  registerNotebookFilestore: (fs: NotebookPostMessageFilestore) => void;
}

export type NotebookControlsKey = keyof Omit<
  NotebookControls,
  "registerNotebookFilestore"
>;
export type NotebookControlsHandler<K extends NotebookControlsKey> =
  NotebookControls[K];

export type InitializationCommand = {
  command: "initialize";
  id: string;
  port: MessagePort;
};

export type RequestConnectionCommand = {
  command: "requestConnection";
  id: string;
};
