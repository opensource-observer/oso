-- AlterEnum
-- This migration adds more than one value to an enum.
-- With PostgreSQL versions 11 and earlier, this is not possible
-- in a single migration. This can be worked around by creating
-- multiple migrations, each migration adding only one value to
-- the enum.


ALTER TYPE "ContributorNamespace" ADD VALUE 'CONTRACT_ADDRESS';
ALTER TYPE "ContributorNamespace" ADD VALUE 'SAFE_ADDRESS';

-- CreateTable
CREATE TABLE "ContributorGroup" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,

    CONSTRAINT "ContributorGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ContributorGroupsOnContributors" (
    "id" SERIAL NOT NULL,
    "contributorId" INTEGER NOT NULL,
    "groupId" INTEGER NOT NULL,

    CONSTRAINT "ContributorGroupsOnContributors_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "ContributorGroupsOnContributors" ADD CONSTRAINT "ContributorGroupsOnContributors_contributorId_fkey" FOREIGN KEY ("contributorId") REFERENCES "Contributor"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ContributorGroupsOnContributors" ADD CONSTRAINT "ContributorGroupsOnContributors_groupId_fkey" FOREIGN KEY ("groupId") REFERENCES "ContributorGroup"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
