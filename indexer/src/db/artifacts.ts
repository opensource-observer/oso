import { AppDataSource } from "./data-source.js";
import { Artifact, EventType, Event } from "./orm-entities.js";
import { DeepPartial } from "typeorm";
import { Range } from "../utils/ranges.js";

export const ArtifactRepository = AppDataSource.getRepository(Artifact).extend({
  async createMany(artifacts: DeepPartial<Artifact>[]) {
    const newArtifacts = Artifact.create(artifacts);
    return await this.insert(newArtifacts);
  },
  async upsertMany(artifacts: DeepPartial<Artifact>[]) {
    const newArtifacts = Artifact.create(artifacts);
    return await this.upsert(newArtifacts, ["name", "namespace"]);
  },
  async mostFrequentContributors(range: Range, eventTypes: EventType[]) {
    const response = (await this.manager
      .createQueryBuilder()
      .select()
      .addSelect("event.from", "contributorId")
      .addSelect("COUNT(event.from)", "count")
      .addSelect("artifact.name", "contributorName")
      .addSelect("artifact.namespace", "contributorNamespace")
      .from(Event, "event")
      .innerJoin("event.from", "artifact")
      .where("event.type = (:...types)", { types: eventTypes })
      .andWhere("event.time >= :startDate", {
        startDate: range.startDate.toUTC().toSQL(),
      })
      .andWhere("event.time < :endDate", {
        endDate: range.endDate.toUTC().toSQL(),
      })
      .addGroupBy("event.from")
      .addGroupBy("artifact.name")
      .addGroupBy("artifact.namespace")
      .having("COUNT(event.from) > 3")
      .orderBy("count", "DESC")
      .getRawMany()) as Array<{
      contributorId: number;
      count: number;
      contributorName: string;
      contributorNamespace: string;
    }>;
    return response;
  },
});

/*
export function streamFindAll(
  prisma: PrismaClient,
  batchSize: number,
  where: Prisma.ArtifactWhereInput,
): Readable {
  let cursorId: number | undefined = undefined;

  // Lazily stolen from: https://github.com/prisma/prisma/issues/5055
  return new Readable({
    objectMode: true,
    highWaterMark: batchSize,
    async read() {
      try {
        const items = await prisma.artifact.findMany({
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
