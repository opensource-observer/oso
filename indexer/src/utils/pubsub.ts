import { EventEmitter } from "node:events";

type PromiseResolvers<T, E> = {
  resolve: (o: T) => void;
  reject: (err: E) => void;
};

/**
 * Allows a simple internal pub sub that can be resolved with promises
 */
export class PromisePubSub<T, E> {
  private topicResolvers: Record<string, PromiseResolvers<T, E>[]>;
  private emitter: EventEmitter;

  constructor() {
    this.topicResolvers = {};
    this.emitter = new EventEmitter();
    this.emitter.on("message", (topic: string, err: E | null, res: T) => {
      const resolvers = this.topicResolvers[topic] || [];
      this.topicResolvers[topic] = [];
      for (const resolver of resolvers) {
        if (err !== null) {
          resolver.reject(err);
        }
        resolver.resolve(res);
      }
    });
  }

  sub(topic: string): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const resolvers = this.topicResolvers[topic] || [];
      resolvers.push({
        resolve: resolve,
        reject: reject,
      });
    });
  }

  pub(topic: string, err: E | null, res?: T) {
    this.emitter.emit("message", topic, err, res);
  }
}
