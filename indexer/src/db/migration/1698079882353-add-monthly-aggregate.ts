import { MigrationInterface, QueryRunner } from "typeorm";

export class AddMonthlyAggregate1698079882353 implements MigrationInterface {
  name = "AddMonthlyAggregate1698079882353";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_monthly_by_artifact" AS 
    SELECT "toId",
      "typeId",
      time_bucket(INTERVAL '1 month', "time") AS "bucketMonthly",
      SUM(amount) as "amount"
    FROM "event" 
    GROUP BY "toId", "typeId", "bucketMonthly"
    WITH NO DATA;
  `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_monthly_by_artifact",
        'SELECT "toId",\n      "typeId",\n      time_bucket(INTERVAL \'1 month\', "time") AS "bucketMonthly",\n      SUM(amount) as "amount"\n    FROM "event" \n    GROUP BY "toId", "typeId", "bucketMonthly"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_monthly_by_project" AS 
    SELECT "projectId",
      "typeId",
      time_bucket(INTERVAL '1 month', "time") AS "bucketMonthly",
      SUM(amount) as "amount"
    FROM "event"
    INNER JOIN "project_artifacts_artifact"
      on "project_artifacts_artifact"."artifactId" = "event"."toId"
    GROUP BY "projectId", "typeId", "bucketMonthly"
    WITH NO DATA;
  `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_monthly_by_project",
        'SELECT "projectId",\n      "typeId",\n      time_bucket(INTERVAL \'1 month\', "time") AS "bucketMonthly",\n      SUM(amount) as "amount"\n    FROM "event"\n    INNER JOIN "project_artifacts_artifact"\n      on "project_artifacts_artifact"."artifactId" = "event"."toId"\n    GROUP BY "projectId", "typeId", "bucketMonthly"\n    WITH NO DATA;',
      ],
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_monthly_by_project", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_monthly_by_project"`,
    );
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_monthly_by_artifact", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_monthly_by_artifact"`,
    );
  }
}
