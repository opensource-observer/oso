import { prisma } from "./prisma-client.js";

export async function getUnsyncedContracts(date: Date) {
  const contracts = await prisma.artifact.findMany({
    select: {
      id: true,
      name: true,
    },
    where: {
      type: "CONTRACT_ADDRESS",
      namespace: "OPTIMISM",
    },
  });
  return contracts;
}
