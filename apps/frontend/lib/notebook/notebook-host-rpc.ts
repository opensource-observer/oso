import { RpcTarget } from "capnweb";
import { NotebookHostControls } from "@/lib/notebook/notebook-controls";

export class NotebookHostRpc extends RpcTarget implements NotebookHostControls {
  private handler?: NotebookHostControls;

  constructor() {
    super();
  }

  async saveNotebook(contents: string): Promise<void> {
    if (!this.handler) {
      throw new Error("No handler registered for host controls");
    }
    return this.handler.saveNotebook(contents);
  }

  async readNotebook(): Promise<string | null> {
    // Reads don't fail if there's no handler, just return null. This allows the
    // notebook to fallback to other filestores, particularly, the fragment
    // store.
    if (!this.handler) {
      return null;
    }
    return this.handler.readNotebook();
  }

  async saveNotebookPreview(base64Image: string): Promise<void> {
    if (!this.handler) {
      throw new Error("No handler registered for host controls");
    }
    return this.handler.saveNotebookPreview(base64Image);
  }

  setHandler(handler: NotebookHostControls) {
    this.handler = handler;
  }
}
