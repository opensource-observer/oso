import {
  And,
  DeepPartial,
  FindOperator,
  FindOptionsWhere,
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
import { logger } from "../utils/logger.js";
import { GenericError } from "../common/errors.js";

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

export type EventTypeRef = Pick<EventType, "name" | "version">;

export type EventRef = Pick<Event, "id" | "sourceId" | "typeId">;

export type BulkUpdateBySourceIDEvent = DeepPartial<Event> &
  Pick<Event, "time" | "sourceId" | "typeId">;

export class BulkUpdateError extends GenericError {}
class BulkUpdateDeletionRecordsMismatch extends GenericError {}

export const EventRepository = AppDataSource.getRepository(Event).extend({
  // Mostly used for testing
  // async findByTypeWithArtifacts(type: EventTypeEnum, addWhere?: FindOptionsWhere<Event>) {
  //   const where: FindOptionsWhere<Event> = {
  //   }

  //   return this.find({
  //     where: where
  //   })
  // },
  async bulkUpdateBySourceIDAndType(events: BulkUpdateBySourceIDEvent[]) {
    // Ensure all have the same event type
    if (events.length === 0) {
      return [];
    }

    const summary = events.reduce<{
      types: Record<string, boolean>;
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
        const eventTypeKey = `${event.typeId}:${event.typeId}`;
        if (!summ.types[eventTypeKey]) {
          summ.types[eventTypeKey] = true;
        }
        summ.sourceIds.push(event.sourceId);
        return summ;
      },
      {
        types: {},
        sourceIds: [],
        range: {
          startDate: DateTime.fromJSDate(events[0].time),
          endDate: DateTime.fromJSDate(events[0].time),
        },
      },
    );
    if (Object.keys(summary.types).length !== 1) {
      throw new BulkUpdateError(
        "bulk update requires event types have the same type",
      );
    }

    const updateTransaction = async (
      queryRange: FindOperator<Date> | undefined,
    ) => {
      return await this.manager.transaction(async (manager) => {
        const repo = manager.withRepository(this);

        // Delete all of the events within the specific time range and with the specific sourceIds
        logger.debug(`deleting ${events.length} event(s) in transaction`);
        const whereOptions: FindOptionsWhere<Event> = {
          sourceId: In(summary.sourceIds),
          typeId: events[0].typeId,
        };
        if (queryRange) {
          whereOptions.time = queryRange;
        }
        const deleteResult = await repo.delete(whereOptions);
        if (!deleteResult.affected) {
          logger.debug(`deletion affected no rows. that is not expected`);
          throw new BulkUpdateError(
            "the deletion should have effected the expected number of rows. no deletions recorded",
          );
        }
        if (deleteResult.affected < summary.sourceIds.length) {
          logger.debug(
            `deletion affected ${deleteResult.affected} rows. expected to delete ${summary.sourceIds.length}`,
          );
          logger.debug(`deleted with ${whereOptions}`);
          throw new BulkUpdateDeletionRecordsMismatch(
            `the deletion should have effected ${summary.sourceIds.length}. Only deleted ${deleteResult.affected}`,
          );
        }

        logger.debug(`reinserting ${events.length} event(s) in transaction`);
        return await repo.insert(events);
      });
    };

    // All a retry with the range Give a larger range in case event dates
    // changed (either we got it wrong our our definitions or data changed).
    // There's retry logic to allow for more but this should hopefully cover 95%
    // of cases
    let rangeToUse: FindOperator<Date> | undefined = And(
      MoreThanOrEqual(summary.range.startDate.minus({ months: 3 }).toJSDate()),
      LessThanOrEqual(summary.range.endDate.plus({ months: 3 }).toJSDate()),
    );
    for (let i = 0; i < 2; i++) {
      try {
        return await updateTransaction(rangeToUse);
      } catch (err) {
        if (err instanceof BulkUpdateDeletionRecordsMismatch) {
          logger.debug(
            "failed to do bulk update due to unexpected affected records. retrying without time range constraint",
          );
          rangeToUse = undefined;
        } else {
          throw err;
        }
      }
    }
    throw new BulkUpdateError(
      `failed to update ${events.length} existing event(s)`,
    );
  },
});
