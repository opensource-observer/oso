-- AlterEnum
ALTER TYPE "ContributorNamespace" ADD VALUE 'GITHUB_ORG';

-- AlterEnum
-- This migration adds more than one value to an enum.
-- With PostgreSQL versions 11 and earlier, this is not possible
-- in a single migration. This can be worked around by creating
-- multiple migrations, each migration adding only one value to
-- the enum.


ALTER TYPE "EventType" ADD VALUE 'FORK_AGGREGATE_STATS';
ALTER TYPE "EventType" ADD VALUE 'FORKED';
ALTER TYPE "EventType" ADD VALUE 'WATCHER_AGGREGATE_STATS';
