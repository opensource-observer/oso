import { MigrationInterface, QueryRunner } from "typeorm";

export class AddTempEventTable1699514548114 implements MigrationInterface {
  name = "AddTempEventTable1699514548114";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE "recording" ("recorderId" uuid NOT NULL, "expiration" TIMESTAMP WITH TIME ZONE NOT NULL, CONSTRAINT "PK_3cbc085e961540e077702c8bc65" PRIMARY KEY ("recorderId"))`,
    );
    await queryRunner.query(
      `CREATE TABLE "recorder_temp_event" ("id" SERIAL NOT NULL, "recorderId" uuid NOT NULL, "batchId" integer NOT NULL, "sourceId" text NOT NULL, "typeId" integer NOT NULL, "time" TIMESTAMP WITH TIME ZONE NOT NULL, "toName" text NOT NULL, "toNamespace" "public"."artifact_namespace_enum" NOT NULL, "toType" "public"."artifact_type_enum" NOT NULL, "toUrl" text, "fromName" text, "fromNamespace" "public"."artifact_namespace_enum", "fromType" "public"."artifact_type_enum", "fromUrl" text, "amount" double precision NOT NULL, "details" jsonb NOT NULL DEFAULT '{}', CONSTRAINT "PK_5dd06a9a9251fe1b43cd3c1967b" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE TABLE "recorder_temp_duplicate_event" ("id" SERIAL NOT NULL, "recorderId" uuid NOT NULL, "typeId" integer NOT NULL, "sourceId" text NOT NULL, CONSTRAINT "PK_aaf868290e25b0361902b1b0c9b" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_c57efc44a97ba219c4ac7b6c15" ON "recorder_temp_duplicate_event" ("typeId", "sourceId", "recorderId") `,
    );
    await queryRunner.query(`CREATE VIEW "recorder_temp_event_artifact" AS 
  WITH to_artifacts AS (
    SELECT
      rte_to."toName" as "name",
      rte_to."toNamespace" as "namespace",
      rte_to."toType" as "type",
      rte_to."toUrl" as "url",
      rte_to."recorderId" as "recorderId",
      rte_to."batchId" as "batchId"
    FROM recorder_temp_event as rte_to
  ),
  from_artifacts AS (
    SELECT
      rte_from."fromName" as "name",
      rte_from."fromNamespace" as "namespace",
      rte_from."fromType" as "type",
      rte_from."fromUrl" as "url",
      rte_from."recorderId" as "recorderId",
      rte_from."batchId" as "batchId"
    FROM recorder_temp_event as rte_from
  ), all_artifacts AS (
    select * from to_artifacts
    UNION
    select * from from_artifacts
  )
  SELECT
    * 
  FROM all_artifacts a
  WHERE 
    a."name" IS NOT NULL AND
    a."namespace" IS NOT NULL AND
    a."type" IS NOT NULL
  `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "VIEW",
        "recorder_temp_event_artifact",
        'WITH to_artifacts AS (\n    SELECT\n      rte_to."toName" as "name",\n      rte_to."toNamespace" as "namespace",\n      rte_to."toType" as "type",\n      rte_to."toUrl" as "url",\n      rte_to."recorderId" as "recorderId",\n      rte_to."batchId" as "batchId"\n    FROM recorder_temp_event as rte_to\n  ),\n  from_artifacts AS (\n    SELECT\n      rte_from."fromName" as "name",\n      rte_from."fromNamespace" as "namespace",\n      rte_from."fromType" as "type",\n      rte_from."fromUrl" as "url",\n      rte_from."recorderId" as "recorderId",\n      rte_from."batchId" as "batchId"\n    FROM recorder_temp_event as rte_from\n  ), all_artifacts AS (\n    select * from to_artifacts\n    UNION\n    select * from from_artifacts\n  )\n  SELECT\n    * \n  FROM all_artifacts a\n  WHERE \n    a."name" IS NOT NULL AND\n    a."namespace" IS NOT NULL AND\n    a."type" IS NOT NULL',
      ],
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["VIEW", "recorder_temp_event_artifact", "public"],
    );
    await queryRunner.query(`DROP VIEW "recorder_temp_event_artifact"`);
    await queryRunner.query(
      `DROP INDEX "public"."IDX_c57efc44a97ba219c4ac7b6c15"`,
    );
    await queryRunner.query(`DROP TABLE "recorder_temp_duplicate_event"`);
    await queryRunner.query(`DROP TABLE "recorder_temp_event"`);
    await queryRunner.query(`DROP TABLE "recording"`);
  }
}
