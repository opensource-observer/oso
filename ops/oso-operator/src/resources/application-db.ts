import * as k8s from "@kubernetes/client-node";
import { ResourceHandler } from "./definition";

interface ApplicationDBSpec {
  databaseName: string;
  engine: string; // e.g., "PostgreSQL", "MySQL"
  version: string;
  storage: number; // in GB
  replicas: number;
  users: DatabaseUserSpec[];
}

interface DatabaseUserSpec {
  username: string;
  role: string; // e.g., "admin", "readonly"
}

interface ApplicationDBStatus {
  phase: string; // e.g., "Pending", "Running", "Failed"
  message?: string;
  endpoint?: string;
  readyReplicas: number;
}

type ApplicationDB = k8s.KubernetesObject & {
  spec: ApplicationDBSpec;
  status?: ApplicationDBStatus;
};


class ApplicationDBHandler extends ResourceHandler<ApplicationDB> {
  public group = "opensource.observer";
  public version = "v1alpha1";
  public plural = "applicationdbs";

  async onCreate(obj: ApplicationDB): Promise<void> {
    console.log(`ApplicationDB created: ${obj?.metadata?.name}`);
  }

  async onUpdate(obj: ApplicationDB): Promise<void> {
    console.log(`ApplicationDB updated: ${obj?.metadata?.name}`);
  }

  async onDelete(obj: ApplicationDB): Promise<void> {
    console.log(`ApplicationDB deleted: ${obj?.metadata?.name}`);
  }
}
