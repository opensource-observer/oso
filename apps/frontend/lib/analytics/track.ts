import { User } from "@/lib/types/user";
import { PostHog } from "posthog-node";
import { PostHogClient } from "@/lib/clients/posthog";

export class PostHogTracker {
  private client: PostHog;
  private user: User;

  constructor(user: User) {
    this.client = PostHogClient();
    this.user = user;
    if (user.role !== "anonymous") {
      this.client.identify({
        distinctId: user.userId,
        properties: {
          name: user.name,
          email: user.email,
        },
      });
    }
  }

  track(eventName: string, properties: Record<string, any> = {}) {
    if (this.user.role === "anonymous") {
      return;
    }

    this.client.capture({
      distinctId: this.user.userId,
      event: eventName,
      properties: {
        ...properties,
        apiKeyName: this.user.keyName,
        host: this.user.host,
        userRole: this.user.role,
      },
    });
  }

  async [Symbol.asyncDispose]() {
    await this.client.shutdown();
  }
}

export function trackServerEvent(user: User) {
  return new PostHogTracker(user);
}
