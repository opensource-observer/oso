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
    // Reads don't fail if there's no handler, just return null
    if (!this.handler) {
      return null;
    }
    return this.handler.readNotebook();
  }

  setHandler(handler: NotebookHostControls) {
    this.handler = handler;
  }
}
