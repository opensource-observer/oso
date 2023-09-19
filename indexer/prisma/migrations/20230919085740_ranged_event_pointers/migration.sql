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

    CONSTRAINT "RangedEventPointer_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "RangedEventPointer_artifactId_collector_startDate_endDate_key" ON "RangedEventPointer"("artifactId", "collector", "startDate", "endDate");

-- AddForeignKey
ALTER TABLE "RangedEventPointer" ADD CONSTRAINT "RangedEventPointer_artifactId_fkey" FOREIGN KEY ("artifactId") REFERENCES "Artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
