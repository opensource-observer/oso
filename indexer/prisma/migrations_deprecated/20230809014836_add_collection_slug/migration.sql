/*
  Warnings:

  - A unique constraint covering the columns `[slug]` on the table `Collection` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `slug` to the `Collection` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "Collection" ADD COLUMN     "slug" TEXT NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "Collection_slug_key" ON "Collection"("slug");
