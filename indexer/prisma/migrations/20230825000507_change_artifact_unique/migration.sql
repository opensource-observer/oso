/*
  Warnings:

  - A unique constraint covering the columns `[namespace,name]` on the table `Artifact` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "Artifact_type_namespace_name_key";

-- CreateIndex
CREATE UNIQUE INDEX "Artifact_namespace_name_key" ON "Artifact"("namespace", "name");
