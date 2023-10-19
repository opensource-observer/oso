import { AppDataSource } from "./data-source.js";
import { Artifact, EventType, Event, ArtifactType } from "./orm-entities.js";
import { DeepPartial } from "typeorm";
import { Range } from "../utils/ranges.js";

export const ArtifactRepository = AppDataSource.getRepository(Artifact).extend({
  async createMany(artifacts: DeepPartial<Artifact>[]) {
    const newArtifacts = Artifact.create(artifacts);
    return await this.insert(newArtifacts);
  },
  async upsertMany(artifacts: DeepPartial<Artifact>[]) {
    const newArtifacts = Artifact.create(artifacts);
    return await this.upsert(newArtifacts, {
      conflictPaths: ["namespace", "name"],
      upsertType: "on-conflict-do-update",
    });
  },
  async nonCanonical(types: ArtifactType[]) {
    const sumString =
      'SUM(CASE WHEN LOWER(a."name") = a."name" THEN 0 ELSE 1 END)';
    return (await this.manager
      .createQueryBuilder()
      .select()
      .addSelect('a."name"', "name")
      .addSelect('a."namespace"', "namespace")
      .addSelect('a."type"', "type")
      .addSelect(sumString, "nonCanonicalCount")
      .from(Artifact, "a")
      .where("a.type IN (:...types)", { types: types })
      .groupBy("1,2,3")
      .having(`${sumString} > 0`)
      .getRawMany()) as {
      name: string;
      namespace: string;
      type: string;
      nonCanonicalCount: number;
    }[];
  },
  async duplicates(types: ArtifactType[]) {
    return (await this.manager
      .createQueryBuilder()
      .select()
      .addSelect('lower(a."name")', "name")
      .addSelect('a."namespace"', "namespace")
      .addSelect('a."type"', "type")
      .addSelect('count(a."id")', "count")
      .addSelect('array_agg(a."id")', "ids")
      .addSelect('array_agg(a."name")', "names")
      .from(Artifact, "a")
      .where("a.type IN (:...types)", { types: types })
      .groupBy("1,2,3")
      .having('count(a."id") > 1')
      .getRawMany()) as {
      name: string;
      namespace: string;
      type: string;
      count: number;
      ids: number[];
      names: string[];
    }[];
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
