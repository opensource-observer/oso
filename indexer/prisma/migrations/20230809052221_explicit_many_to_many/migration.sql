/*
  Warnings:

  - You are about to drop the `_ArtifactToProject` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `_CollectionToProject` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "_ArtifactToProject" DROP CONSTRAINT "_ArtifactToProject_A_fkey";

-- DropForeignKey
ALTER TABLE "_ArtifactToProject" DROP CONSTRAINT "_ArtifactToProject_B_fkey";

-- DropForeignKey
ALTER TABLE "_CollectionToProject" DROP CONSTRAINT "_CollectionToProject_A_fkey";

-- DropForeignKey
ALTER TABLE "_CollectionToProject" DROP CONSTRAINT "_CollectionToProject_B_fkey";

-- DropTable
DROP TABLE "_ArtifactToProject";

-- DropTable
DROP TABLE "_CollectionToProject";

-- CreateTable
CREATE TABLE "CollectionsOnProjects" (
    "assignedAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "collectionId" INTEGER NOT NULL,
    "projectId" INTEGER NOT NULL,

    CONSTRAINT "CollectionsOnProjects_pkey" PRIMARY KEY ("collectionId","projectId")
);

-- CreateTable
CREATE TABLE "ProjectsOnArtifacts" (
    "assignedAt" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "projectId" INTEGER NOT NULL,
    "artifactId" INTEGER NOT NULL,

    CONSTRAINT "ProjectsOnArtifacts_pkey" PRIMARY KEY ("projectId","artifactId")
);

-- AddForeignKey
ALTER TABLE "CollectionsOnProjects" ADD CONSTRAINT "CollectionsOnProjects_collectionId_fkey" FOREIGN KEY ("collectionId") REFERENCES "Collection"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CollectionsOnProjects" ADD CONSTRAINT "CollectionsOnProjects_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectsOnArtifacts" ADD CONSTRAINT "ProjectsOnArtifacts_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProjectsOnArtifacts" ADD CONSTRAINT "ProjectsOnArtifacts_artifactId_fkey" FOREIGN KEY ("artifactId") REFERENCES "Artifact"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
