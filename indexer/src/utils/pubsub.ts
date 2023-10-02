import { EventEmitter } from "node:events";
import { logger } from "./logger.js";
import _ from "lodash";
import { GenericError } from "../common/errors.js";

type PromiseResolvers<T, E> = {
  resolve: (o: T) => void;
  reject: (err: E) => void;
  timeout: NodeJS.Timeout | null;
};

export interface PromisePubSubOptions {
  timeoutMs: number;
}

export class PromisePubSubTimeoutError extends GenericError {}

/**
 * Allows a simple internal pub sub that can be resolved with promises
 */
export class PromisePubSub<T, E> {
  private topicResolvers: Record<string, PromiseResolvers<T, E>[]>;
  private emitter: EventEmitter;
  private options: PromisePubSubOptions;

  constructor(options?: PromisePubSubOptions) {
    this.topicResolvers = {};
    this.emitter = new EventEmitter();
    this.options = _.merge(
      {
        timeoutMs: 0,
      },
      options,
    );
    this.emitter.on("message", (topic: string, err: E | null, res: T) => {
      const resolvers = this.topicResolvers[topic] || [];
      this.topicResolvers[topic] = [];

      for (const resolver of resolvers) {
        try {
          if (err !== null) {
            resolver.reject(err);
          }
          resolver.resolve(res);

          if (resolver.timeout) {
            clearTimeout(resolver.timeout);
          }
        } catch (err) {
          logger.error("Unexpectedly errored resolving pub sub promises");
        }
      }
    });
  }

  sub(topic: string): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const resolvers = this.topicResolvers[topic] || [];
      const timeout =
        this.options.timeoutMs <= 0
          ? null
          : setTimeout(() => {
              reject(new PromisePubSubTimeoutError(`timeout for ${topic}`));
            }, this.options.timeoutMs);

      resolvers.push({
        resolve: resolve,
        reject: reject,
        timeout: timeout,
      });
      this.topicResolvers[topic] = resolvers;
    });
  }

  pub(topic: string, err: E | null, res?: T) {
    this.emitter.emit("message", topic, err, res);
  }
}
