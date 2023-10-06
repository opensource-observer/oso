import { Artifact, EventPointer } from "../db/orm-entities.js";
import { Range } from "../utils/ranges.js";
import { asyncBatch } from "../utils/array.js";
import _ from "lodash";
import { EventPointerRepository } from "../db/events.js";
import { DataSource, In, LessThan, MoreThanOrEqual } from "typeorm";
import { logger } from "../utils/logger.js";

type IEventPointerRepository = typeof EventPointerRepository;

export interface EventPointerManagerOptions {
  batchSize: number;
}

export const DefaultEventPointerManagerOptions = {
  batchSize: 5000,
};

// Event pointer management
export class EventPointerManager {
  private eventPointerRepository: IEventPointerRepository;
  private options: EventPointerManagerOptions;
  private dataSource: DataSource;

  constructor(
    dataSource: DataSource,
    eventPointerRepository: IEventPointerRepository,
    options?: EventPointerManagerOptions,
  ) {
    this.eventPointerRepository = eventPointerRepository;
    this.dataSource = dataSource;
    this.options = _.merge(DefaultEventPointerManagerOptions, options);
  }

  // Find all matching event pointers for the given artifacts and the collector
  // name
  async getAllEventPointersForRange(
    range: Range,
    artifacts: Artifact[],
    collector: string,
  ): Promise<EventPointer[]> {
    const batches = await asyncBatch(
      artifacts,
      this.options.batchSize,
      async (batch) => {
        return this.eventPointerRepository.find({
          // where (range.startDate <= startDate < range.endDate) || (range.startDate < endDate <= range.endDate)
          relations: {
            artifact: true,
          },
          where: {
            collector: collector,
            artifact: {
              id: In(batch.map((a) => a.id)),
            },
            startDate: LessThan(range.endDate.toJSDate()),
            endDate: MoreThanOrEqual(range.startDate.toJSDate()),
          },
        });
      },
    );
    return batches.flat(1);
  }

  async commitArtifactForRange(
    range: Range,
    artifact: Artifact,
    collector: string,
  ) {
    logger.debug(`committing this artifact[${artifact.id}]`);

    // Find any old event pointer that's connectable to this one if it exists. Update it.
    const intersectingPointers = await this.getAllEventPointersForRange(
      range,
      [artifact],
      collector,
    );

    if (intersectingPointers.length === 0) {
      // Create a new pointer
      const pointer = this.eventPointerRepository.create({
        startDate: range.startDate.toJSDate(),
        endDate: range.endDate.toJSDate(),
        collector: collector,
        artifact: { id: artifact.id },
        version: 0,
      });
      await this.eventPointerRepository.insert(pointer);
      return;
    } else {
      // Order all of the intersecting pointers by start date and also by end date
      // Start date ascending
      const byStartDate = _.clone(intersectingPointers).sort(
        (a, b) => a.startDate.getTime() - b.startDate.getTime(),
      );

      // End date descending
      const byEndDate = _.clone(intersectingPointers).sort(
        (a, b) => b.endDate.getTime() - a.endDate.getTime(),
      );

      const startDate =
        byStartDate[0].startDate.getTime() <
        range.startDate.toJSDate().getTime()
          ? byStartDate[0].startDate
          : range.startDate.toJSDate();
      const endDate =
        byEndDate[0].endDate.getTime() > range.endDate.toJSDate().getTime()
          ? byEndDate[0].endDate
          : range.endDate.toJSDate();

      // Merge all of the pointers (arbitrarily choose the first and delete the others)
      return this.dataSource.transaction(async (manager) => {
        const repository = manager.withRepository(this.eventPointerRepository);

        await repository.update(
          {
            artifact: {
              id: artifact.id,
            },
            id: byStartDate[0].id,
            version: byStartDate[0].version,
          },
          {
            artifact: {
              id: artifact.id,
            },
            startDate: startDate,
            endDate: endDate,
            version: byStartDate[0].version + 1,
          },
        );

        await Promise.all(
          byStartDate.slice(1).map((p) => {
            return repository.delete({
              id: p.id,
              version: p.version,
            });
          }),
        );
      });
    }
  }
}
