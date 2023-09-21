import { Artifact, PrismaClient, RangedEventPointer } from "@prisma/client";
import { Range } from "../utils/ranges.js";
import { asyncBatch } from "../utils/array.js";
import _ from "lodash";

export interface EventPointerManagerOptions {
  batchSize: number;
}

export const DefaultEventPointerManagerOptions = {
  batchSize: 5000,
};

// Event pointer management
export class EventPointerManager {
  private prisma: PrismaClient;
  private options: EventPointerManagerOptions;

  constructor(prisma: PrismaClient, options?: EventPointerManagerOptions) {
    this.prisma = prisma;
    this.options = _.merge(DefaultEventPointerManagerOptions, options);
  }

  // Find all matching event pointers for the given artifacts and the collector
  // name
  async getAllEventPointersForRange(
    range: Range,
    artifacts: Artifact[],
    collector: string,
  ): Promise<RangedEventPointer[]> {
    const batches = await asyncBatch(
      artifacts,
      this.options.batchSize,
      async (batch) => {
        return this.prisma.rangedEventPointer.findMany({
          where: {
            collector: {
              equals: collector,
            },
            artifactId: {
              in: batch.map((a) => a.id),
            },
            OR: [
              {
                startDate: {
                  gte: range.startDate.toJSDate(),
                  lt: range.endDate.toJSDate(),
                },
              },
              {
                endDate: {
                  gt: range.startDate.toJSDate(),
                  lte: range.endDate.toJSDate(),
                },
              },
            ],
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
    // Find any old event pointer that's connectable to this one if it exists. Update it.
    const intersectingPointers = await this.prisma.rangedEventPointer.findMany({
      where: {
        collector: {
          equals: collector,
        },
        artifactId: {
          equals: artifact.id,
        },
        OR: [
          // endDate >= range.startDate || startDate <= range.endDate
          {
            endDate: {
              gte: range.startDate.toJSDate(),
            },
          },
          {
            startDate: {
              lte: range.endDate.toJSDate(),
            },
          },
        ],
      },
    });

    if (intersectingPointers.length === 0) {
      // Create a new pointer
      return this.prisma.rangedEventPointer.create({
        data: {
          startDate: range.startDate.toJSDate(),
          endDate: range.endDate.toJSDate(),
          collector: collector,
          artifactId: artifact.id,
          pointer: {},
          version: 0,
        },
      });
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
      const update = this.prisma.rangedEventPointer.update({
        where: {
          id: byStartDate[0].id,
          version: byStartDate[0].version,
        },
        data: {
          startDate: startDate,
          endDate: endDate,
          version: {
            increment: 1,
          },
        },
      });
      const deletions = byStartDate.slice(1).map((p) => {
        return this.prisma.rangedEventPointer.delete({
          where: {
            id: p.id,
            version: p.version,
          },
        });
      });

      return await this.prisma.$transaction([update, ...deletions]);
    }
  }
}
