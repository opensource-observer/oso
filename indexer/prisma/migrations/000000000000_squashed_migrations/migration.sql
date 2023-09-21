-- Setup TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- CreateEnum
CREATE TYPE "EventType" AS ENUM ('FUNDING', 'PULL_REQUEST_CREATED', 'PULL_REQUEST_MERGED', 'COMMIT_CODE', 'ISSUE_FILED', 'ISSUE_CLOSED', 'DOWNSTREAM_DEPENDENCY_COUNT', 'UPSTREAM_DEPENDENCY_COUNT', 'DOWNLOADS', 'CONTRACT_INVOKED', 'USERS_INTERACTED', 'CONTRACT_INVOKED_AGGREGATE_STATS', 'PULL_REQUEST_CLOSED', 'STAR_AGGREGATE_STATS', 'PULL_REQUEST_REOPENED', 'PULL_REQUEST_REMOVED_FROM_PROJECT', 'PULL_REQUEST_APPROVED', 'ISSUE_CREATED', 'ISSUE_REOPENED', 'ISSUE_REMOVED_FROM_PROJECT', 'STARRED', 'FORK_AGGREGATE_STATS', 'FORKED', 'WATCHER_AGGREGATE_STATS');

-- CreateEnum
CREATE TYPE "ArtifactType" AS ENUM ('EOA_ADDRESS', 'SAFE_ADDRESS', 'CONTRACT_ADDRESS', 'GIT_REPOSITORY', 'NPM_PACKAGE', 'FACTORY_ADDRESS');

-- CreateEnum
CREATE TYPE "ArtifactNamespace" AS ENUM ('ETHEREUM', 'OPTIMISM', 'GOERLI', 'GITHUB', 'GITLAB', 'NPM_REGISTRY');

-- CreateEnum
CREATE TYPE "ContributorNamespace" AS ENUM ('GITHUB_USER', 'EOA_ADDRESS', 'GIT_EMAIL', 'GIT_NAME', 'GITHUB_ORG', 'CONTRACT_ADDRESS', 'SAFE_ADDRESS');

-- CreateEnum
CREATE TYPE "JobStatus" AS ENUM ('PENDING', 'COMPLETE');

-- CreateEnum
CREATE TYPE "JobExecutionStatus" AS ENUM ('ACTIVE', 'COMPLETE', 'FAILED');

-- CreateTable
CREATE TABLE "Collection" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "verified" BOOLEAN NOT NULL DEFAULT false,
    "slug" TEXT NOT NULL,

    CONSTRAINT "Collection_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CollectionsOnProjects" (
    "assignedAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "collectionId" INTEGER NOT NULL,
    "projectId" INTEGER NOT NULL,

    CONSTRAINT "CollectionsOnProjects_pkey" PRIMARY KEY ("collectionId","projectId")
);

-- CreateTable
CREATE TABLE "Project" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "verified" BOOLEAN NOT NULL DEFAULT false,
    "slug" TEXT NOT NULL,

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ProjectsOnArtifacts" (
    "assignedAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "projectId" INTEGER NOT NULL,
    "artifactId" INTEGER NOT NULL,

    CONSTRAINT "ProjectsOnArtifacts_pkey" PRIMARY KEY ("projectId","artifactId")
);

-- CreateTable
CREATE TABLE "Artifact" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "type" "ArtifactType" NOT NULL,
    "namespace" "ArtifactNamespace" NOT NULL,
    "name" TEXT NOT NULL,
    "url" TEXT,
    "details" JSONB,

    CONSTRAINT "Artifact_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventTs" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "type" "EventType" NOT NULL,
    "time" TIMESTAMPTZ(3) NOT NULL,
    "toArtifactId" INTEGER NOT NULL,
    "fromArtifactId" INTEGER,
    "amount" DOUBLE PRECISION NOT NULL
);

-- CreateTable
CREATE TABLE "RangedEventPointer" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "artifactId" INTEGER NOT NULL,
    "collector" TEXT NOT NULL,
    "pointer" JSONB NOT NULL,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "version" INTEGER NOT NULL,

    CONSTRAINT "RangedEventPointer_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Job" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "execGroup" TEXT NOT NULL,
    "scheduledTime" TIMESTAMP(3) NOT NULL,
    "collector" TEXT NOT NULL,
    "status" "JobStatus" NOT NULL,

    CONSTRAINT "Job_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "JobExecution" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "status" "JobExecutionStatus" NOT NULL,
    "details" JSONB,
    "jobId" INTEGER NOT NULL,

    CONSTRAINT "JobExecution_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Log" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "executionId" INTEGER NOT NULL,
    "level" TEXT NOT NULL,
    "body" JSONB NOT NULL,

    CONSTRAINT "Log_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Collection_slug_key" ON "Collection"("slug");

-- CreateIndex
CREATE UNIQUE INDEX "Project_slug_key" ON "Project"("slug");

-- CreateIndex
CREATE UNIQUE INDEX "Artifact_namespace_name_key" ON "Artifact"("namespace", "name");

-- CreateIndex
CREATE UNIQUE INDEX "EventTs_id_time_key" ON "EventTs"("id", "time");

-- CreateIndex
CREATE UNIQUE INDEX "RangedEventPointer_artifactId_collector_startDate_endDate_key" ON "RangedEventPointer"("artifactId", "collector", "startDate", "endDate");

-- AddForeignKey
ALTER TABLE "CollectionsOnProjects" ADD CONSTRAINT "CollectionsOnProjects_collectionId_fkey" FOREIGN KEY ("collectionId") REFERENCES "Collection"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollectionsOnProjects" ADD CONSTRAINT "CollectionsOnProjects_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectsOnArtifacts" ADD CONSTRAINT "ProjectsOnArtifacts_artifactId_fkey" FOREIGN KEY ("artifactId") REFERENCES "Artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectsOnArtifacts" ADD CONSTRAINT "ProjectsOnArtifacts_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventTs" ADD CONSTRAINT "EventTs_toArtifactId_fkey" FOREIGN KEY ("toArtifactId") REFERENCES "Artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventTs" ADD CONSTRAINT "EventTs_fromArtifactId_fkey" FOREIGN KEY ("fromArtifactId") REFERENCES "Artifact"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RangedEventPointer" ADD CONSTRAINT "RangedEventPointer_artifactId_fkey" FOREIGN KEY ("artifactId") REFERENCES "Artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "JobExecution" ADD CONSTRAINT "JobExecution_jobId_fkey" FOREIGN KEY ("jobId") REFERENCES "Job"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Log" ADD CONSTRAINT "Log_executionId_fkey" FOREIGN KEY ("executionId") REFERENCES "JobExecution"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- Create Hypertable
SELECT create_hypertable('"EventTs"', 'time');