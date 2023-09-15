import { Readable } from "stream";
import { Prisma, PrismaClient, ArtifactType } from "@prisma/client";

export async function allFundableProjectAddresses(prisma: PrismaClient) {
  return await prisma.project.findMany({
    include: {
      artifacts: {
        include: {
          artifact: true,
        },
        where: {
          artifact: {
            type: {
              in: [
                ArtifactType.EOA_ADDRESS,
                ArtifactType.SAFE_ADDRESS,
                ArtifactType.CONTRACT_ADDRESS,
              ],
            },
          },
        },
      },
    },
  });
}

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
