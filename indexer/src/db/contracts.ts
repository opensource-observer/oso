import {
  PrismaClient,
  EventType,
  ArtifactType,
  ArtifactNamespace,
} from "@prisma/client";
import { DateTime, Duration } from "luxon";

export async function getSyncedContracts(prisma: PrismaClient, date: DateTime) {
  const unsyncedContracts = await prisma.artifact.findMany({
    select: {
      id: true,
      name: true,
    },
    where: {
      type: ArtifactType.CONTRACT_ADDRESS,
      namespace: ArtifactNamespace.OPTIMISM,
      eventPtrs: {
        some: {
          updatedAt: {
            gte: date.startOf("day").toJSDate(),
          },
        },
      },
    },
  });
  return unsyncedContracts;
}

export async function getMonitoredContracts(prisma: PrismaClient) {
  const unsyncedContracts = await prisma.artifact.findMany({
    select: {
      id: true,
      name: true,
    },
    where: {
      type: ArtifactType.CONTRACT_ADDRESS,
      namespace: ArtifactNamespace.OPTIMISM,
    },
  });
  return unsyncedContracts;
}

export async function getKnownUserAddressesWithinTimeFrame(
  prisma: PrismaClient,
  start: DateTime,
  end: DateTime,
  limit: number,
) {
  // We want to find all the known addresses and count the number of contracts
  // they use. This function is mostly used to reduce the size of calls to dune.
  // by providing dune with input and IDs that we can use to process data.

  const mostActiveUsersInTimeFrame = await prisma.event.groupBy({
    by: ["contributorId"],
    _count: {
      artifactId: true,
    },
    where: {
      contributorId: { not: null },
      eventType: EventType.CONTRACT_INVOKED,
      artifact: {
        type: ArtifactType.CONTRACT_ADDRESS,
        namespace: ArtifactNamespace.OPTIMISM,
      },
    },
    orderBy: {
      _count: {
        artifactId: "desc",
      },
    },
    take: limit,
  });

  // Resolve the user addresses based on their activity
  // Unfortunately we can't do this in a single query with prisma without raw
  // SQL. Too lazy for now. Hopefully this isn't super taxing on our supabase
  const knownUserAddresses = await prisma.contributor.findMany({
    select: {
      id: true,
      name: true,
    },
    where: {
      id: {
        in: mostActiveUsersInTimeFrame.map((u) => u.contributorId as number),
      },
    },
  });

  return knownUserAddresses;
}
