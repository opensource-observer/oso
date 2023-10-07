import { DeepPartial } from "typeorm";
import { normalizeToObject } from "../utils/common.js";
import { AppDataSource } from "./data-source.js";
import type { Brand } from "utility-types";
import { EventPointer, Event } from "./orm-entities.js";

export const EventPointerRepository = AppDataSource.getRepository(
  EventPointer,
).extend({
  async getPointer<T>(
    artifactId: Brand<number, "ArtifactId">,
    collector: string,
  ) {
    const record = await this.findOne({
      relations: {
        artifact: true,
      },
      where: {
        artifact: {
          id: artifactId,
        },
        collector: collector,
      },
    });
    if (!record) {
      return null;
    }
    // Safe because `Partial` means they're all optional props anyway
    return normalizeToObject<T>(record);
  },
});

export type BulkUpdateBySourceIDEvent = DeepPartial<Event> &
  Pick<Event, "sourceId">;

export const EventRepository = AppDataSource.getRepository(Event).extend({
  async bulkUpdateBySourceID(events: BulkUpdateBySourceIDEvent[]) {
    // This should likely be refactored eventually as this is likely slow.
    return this.manager.transaction(async (manager) => {
      const repo = manager.withRepository(this);
      const results = [];
      for (const event of events) {
        // Add all of the event updates to the transasction
        results.push(
          repo.update(
            {
              sourceId: event.sourceId,
            },
            event,
          ),
        );
      }
      return await Promise.all(results);
    });
  },
});
