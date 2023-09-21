-- CreateEnum
CREATE TYPE "JobStatus" AS ENUM ('PENDING', 'COMPLETE');

-- CreateEnum
CREATE TYPE "JobExecutionStatus" AS ENUM ('ACTIVE', 'COMPLETE', 'FAILED');

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

-- AddForeignKey
ALTER TABLE "JobExecution" ADD CONSTRAINT "JobExecution_jobId_fkey" FOREIGN KEY ("jobId") REFERENCES "Job"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Log" ADD CONSTRAINT "Log_executionId_fkey" FOREIGN KEY ("executionId") REFERENCES "JobExecution"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
