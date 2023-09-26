import _ from "lodash";
import { Readable } from "stream";
import { assert, normalizeToObject } from "../utils/common.js";
import { AppDataSource } from "./data-source.js";
import type { Brand } from "utility-types";
import { EventType, EventPointer, Event } from "./orm-entities.js";

export const EventPointerRepository = AppDataSource.getRepository(
  EventPointer,
).extend({
  async getPointer<PointerType>(
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
    // Safe because `Partial` means they're all optional props anyway
    return normalizeToObject<PointerType>(record?.pointer);
  },
});

export const EventRepository = AppDataSource.getRepository(Event);

/*
export function streamFindAll(
  prisma: PrismaClient,
  batchSize: number,
  where: Prisma.EventWhereInput,
): Readable {
  let cursorId: number | undefined = undefined;

  // Lazily stolen from: https://github.com/prisma/prisma/issues/5055
  return new Readable({
    objectMode: true,
    highWaterMark: batchSize,
    async read() {
      try {
        const items = await prisma.event.findMany({
          where: where,
          take: batchSize,
          skip: cursorId ? 1 : 0,
          cursor: cursorId ? { id: cursorId } : undefined,
        });
        for (const item of items) {
          this.push(item);
        }
        if (items.length < batchSize) {
          this.push(null);
          return;
        }
        const item = items[items.length - 1];
        cursorId = item.id;
      } catch (err) {
        this.destroy(err as any);
      }
    },
  });
}
*/
