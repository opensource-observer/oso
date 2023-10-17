import {
  And,
  DeepPartial,
  In,
  LessThanOrEqual,
  MoreThanOrEqual,
} from "typeorm";
import { normalizeToObject } from "../utils/common.js";
import { AppDataSource } from "./data-source.js";
import type { Brand } from "utility-types";
import { EventPointer, Event, EventType } from "./orm-entities.js";
import { Range } from "../utils/ranges.js";
import { DateTime } from "luxon";

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
  Pick<Event, "time" | "type" | "sourceId">;

export type EventRef = Pick<Event, "id" | "sourceId"> & {
  type: Pick<EventType, "name" | "version">;
};

export const EventRepository = AppDataSource.getRepository(Event).extend({
  async bulkUpdateBySourceIDAndType(events: BulkUpdateBySourceIDEvent[]) {
    // Ensure all have the same event type
    if (events.length === 0) {
      return [];
    }

    const summary = events.reduce<{
      types: EventType[];
      sourceIds: string[];
      range: Range;
    }>(
      (summ, event) => {
        const time = DateTime.fromJSDate(event.time);
        if (time < summ.range.startDate) {
          summ.range.startDate = time;
        }
        if (time > summ.range.endDate) {
          summ.range.endDate = time;
        }
        if (summ.types.indexOf(event.type) === -1) {
          summ.types.push(event.type);
        }
        summ.sourceIds.push(event.sourceId);
        return summ;
      },
      {
        types: [],
        sourceIds: [],
        range: {
          startDate: DateTime.fromJSDate(events[0].time),
          endDate: DateTime.fromJSDate(events[0].time),
        },
      },
    );

    if (summary.types.length !== 1) {
      throw new Error("bulk update requires event types have the same type");
    }

    // This should likely be refactored eventually as this is likely slow
    return this.manager.transaction(async (manager) => {
      const repo = manager.withRepository(this);

      // Delete all of the events within the specific time range and with the specific sourceIds
      const deleteResult = await repo.delete({
        time: And(
          MoreThanOrEqual(summary.range.startDate.toJSDate()),
          LessThanOrEqual(summary.range.endDate.toJSDate()),
        ),
        sourceId: In(summary.sourceIds),
        type: {
          id: summary.types[0].id,
        },
      });
      if (!deleteResult.affected) {
        throw new Error(
          "the deletion should have effected the expected number of rows. no deletions recorded",
        );
      }
      if (deleteResult.affected !== summary.sourceIds.length) {
        throw new Error(
          "the deletion should have effected the expected number of rows",
        );
      }

      return await repo.insert(events);
    });
  },
});
