import * as k8s from "@kubernetes/client-node";

export interface IResourceHandler<T extends k8s.KubernetesObject> {
  group: string;
  version: string;
  plural: string;
  namespace?: string;

  onCreate(obj: T): Promise<void>;
  onUpdate(obj: T): Promise<void>;
  onDelete(obj: T): Promise<void>;
}

export class ResourceHandler<T extends k8s.KubernetesObject> implements IResourceHandler<T> {
  public group: string;
  public version: string;
  public plural: string;
  public namespace?: string;

  async onCreate(obj: T): Promise<void> {
    throw new Error("Method not implemented.");
  }

  async onUpdate(obj: T): Promise<void> {
    throw new Error("Method not implemented.");
  }

  async onDelete(obj: T): Promise<void> {
    throw new Error("Method not implemented.");
  }
}