/*
  Warnings:

  - You are about to drop the column `organizationId` on the `Artifact` table. All the data in the column will be lost.
  - You are about to drop the `EventSourcePointer` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `Organization` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "Artifact" DROP CONSTRAINT "Artifact_organizationId_fkey";

-- DropForeignKey
ALTER TABLE "EventSourcePointer" DROP CONSTRAINT "EventSourcePointer_artifactId_fkey";

-- AlterTable
ALTER TABLE "Artifact" DROP COLUMN "organizationId";

-- DropTable
DROP TABLE "EventSourcePointer";

-- DropTable
DROP TABLE "Organization";

-- CreateTable
CREATE TABLE "Collection" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "verified" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "Collection_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Project" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "verified" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventPointer" (
    "id" SERIAL NOT NULL,
    "createdAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "artifactId" INTEGER NOT NULL,
    "eventType" "EventType" NOT NULL,
    "pointer" JSONB NOT NULL,
    "autocrawl" BOOLEAN,

    CONSTRAINT "EventPointer_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "_CollectionToProject" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "_ArtifactToProject" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "EventPointer_artifactId_eventType_key" ON "EventPointer"("artifactId", "eventType");

-- CreateIndex
CREATE UNIQUE INDEX "_CollectionToProject_AB_unique" ON "_CollectionToProject"("A", "B");

-- CreateIndex
CREATE INDEX "_CollectionToProject_B_index" ON "_CollectionToProject"("B");

-- CreateIndex
CREATE UNIQUE INDEX "_ArtifactToProject_AB_unique" ON "_ArtifactToProject"("A", "B");

-- CreateIndex
CREATE INDEX "_ArtifactToProject_B_index" ON "_ArtifactToProject"("B");

-- AddForeignKey
ALTER TABLE "EventPointer" ADD CONSTRAINT "EventPointer_artifactId_fkey" FOREIGN KEY ("artifactId") REFERENCES "Artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CollectionToProject" ADD CONSTRAINT "_CollectionToProject_A_fkey" FOREIGN KEY ("A") REFERENCES "Collection"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_CollectionToProject" ADD CONSTRAINT "_CollectionToProject_B_fkey" FOREIGN KEY ("B") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_ArtifactToProject" ADD CONSTRAINT "_ArtifactToProject_A_fkey" FOREIGN KEY ("A") REFERENCES "Artifact"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_ArtifactToProject" ADD CONSTRAINT "_ArtifactToProject_B_fkey" FOREIGN KEY ("B") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;
