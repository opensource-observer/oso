import Operator from "@dot-i/k8s-operator";
import { ResourceEventType } from "@dot-i/k8s-operator";
import * as k8s from "@kubernetes/client-node";
import { IResourceHandler } from "./resources/definition";

class OSOOperator extends Operator {
  private resourceHandlers: IResourceHandler<any>[];

  constructor(resourceHandlers: IResourceHandler<any>[]) {
    super();
    this.resourceHandlers = resourceHandlers;
  }

  protected async init() {
    // Register resource handlers
    this.resourceHandlers.forEach((handler) => {
      this.registerResourceHandler(handler);
    });
  }

  private registerResourceHandler<T extends k8s.KubernetesObject>(handler: IResourceHandler<T>) {
    this.watchResource(handler.group, handler.version, handler.plural, async (event) => {
      const obj = event.object as T;
      switch (event.type) {
        case ResourceEventType.Added:
          await handler.onCreate(obj);
          break;
        case ResourceEventType.Modified:
          await handler.onUpdate(obj);
          break;
        case ResourceEventType.Deleted:
          await handler.onDelete(obj);
          break;
      }
    }, handler.namespace);
  }
}

//new ApplicationDBOperator().start();
async function main() {
  const operator = new OSOOperator([
  ]);
  await operator.start();

  const exit = (reason: string) => {
    operator.stop();
    process.exit(0);
  };

  process.on('SIGTERM', () => exit('SIGTERM'))
    .on('SIGINT', () => exit('SIGINT'));
}