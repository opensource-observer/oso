/*
  Warnings:

  - You are about to drop the column `artifactId` on the `EventTs` table. All the data in the column will be lost.
  - You are about to drop the column `contributorId` on the `EventTs` table. All the data in the column will be lost.
  - You are about to drop the column `details` on the `EventTs` table. All the data in the column will be lost.
  - Added the required column `toArtifactId` to the `EventTs` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "EventTs" DROP CONSTRAINT "EventTs_artifactId_fkey";

-- DropForeignKey
ALTER TABLE "EventTs" DROP CONSTRAINT "EventTs_contributorId_fkey";

-- AlterTable
ALTER TABLE "EventTs" DROP COLUMN "artifactId",
DROP COLUMN "contributorId",
DROP COLUMN "details",
ADD COLUMN     "fromArtifactId" INTEGER,
ADD COLUMN     "toArtifactId" INTEGER NOT NULL;

-- AddForeignKey
ALTER TABLE "EventTs" ADD CONSTRAINT "EventTs_toArtifactId_fkey" FOREIGN KEY ("toArtifactId") REFERENCES "Artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventTs" ADD CONSTRAINT "EventTs_fromArtifactId_fkey" FOREIGN KEY ("fromArtifactId") REFERENCES "Artifact"("id") ON DELETE SET NULL ON UPDATE CASCADE;
