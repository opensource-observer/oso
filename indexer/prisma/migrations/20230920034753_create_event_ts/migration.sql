-- Setup TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- CreateTable
CREATE TABLE "EventTs" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "artifactId" INTEGER NOT NULL,
    "type" "EventType" NOT NULL,
    "time" TIMESTAMPTZ(3) NOT NULL,
    "contributorId" INTEGER,
    "amount" DOUBLE PRECISION NOT NULL,
    "details" JSONB
);

-- CreateIndex
CREATE UNIQUE INDEX "EventTs_id_time_key" ON "EventTs"("id", "time");

-- AddForeignKey
ALTER TABLE "EventTs" ADD CONSTRAINT "EventTs_artifactId_fkey" FOREIGN KEY ("artifactId") REFERENCES "Artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventTs" ADD CONSTRAINT "EventTs_contributorId_fkey" FOREIGN KEY ("contributorId") REFERENCES "Contributor"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- Create Hypertable
SELECT create_hypertable('"EventTs"', 'time');