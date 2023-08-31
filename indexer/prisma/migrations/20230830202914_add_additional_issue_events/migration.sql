-- AlterEnum
-- This migration adds more than one value to an enum.
-- With PostgreSQL versions 11 and earlier, this is not possible
-- in a single migration. This can be worked around by creating
-- multiple migrations, each migration adding only one value to
-- the enum.


ALTER TYPE "EventType" ADD VALUE 'PULL_REQUEST_REOPENED';
ALTER TYPE "EventType" ADD VALUE 'PULL_REQUEST_REMOVED_FROM_PROJECT';
ALTER TYPE "EventType" ADD VALUE 'PULL_REQUEST_APPROVED';
ALTER TYPE "EventType" ADD VALUE 'ISSUE_CREATED';
ALTER TYPE "EventType" ADD VALUE 'ISSUE_REOPENED';
ALTER TYPE "EventType" ADD VALUE 'ISSUE_REMOVED_FROM_PROJECT';
