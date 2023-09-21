/*
  Warnings:

  - A unique constraint covering the columns `[name,namespace]` on the table `Contributor` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "Contributor_name_namespace_key" ON "Contributor"("name", "namespace");
