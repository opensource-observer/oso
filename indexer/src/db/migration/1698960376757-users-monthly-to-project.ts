import { MigrationInterface, QueryRunner } from "typeorm";

export class UsersMonthlyToProject1698960376757 implements MigrationInterface {
  name = "UsersMonthlyToProject1698960376757";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE MATERIALIZED VIEW "users_monthly_to_project" AS
    WITH Devs AS (
      SELECT 
        p."id" AS "projectId",
        e."fromId" AS "fromId",
        time_bucket(INTERVAL '1 month', e."time") AS "bucketMonthly",
        CASE 
          WHEN COUNT(DISTINCT CASE WHEN t."name" = 'COMMIT_CODE' THEN e."time" END) >= 10 THEN 'FULL_TIME_DEV'
          WHEN COUNT(DISTINCT CASE WHEN t."name" = 'COMMIT_CODE' THEN e."time" END) >= 1 THEN 'PART_TIME_DEV'
          ELSE 'OTHER_CONTRIBUTOR'
        END AS "segmentType",
        1 AS amount
      FROM event e
      JOIN project_artifacts_artifact paa ON e."toId" = paa."artifactId"
      JOIN project p ON paa."projectId" = p.id        
      JOIN event_type t ON e."typeId" = t.id
      WHERE
        t."name" IN (
          'PULL_REQUEST_CREATED',
          'PULL_REQUEST_MERGED',
          'COMMIT_CODE',
          'ISSUE_CLOSED',
          'ISSUE_CREATED'
        )
      GROUP BY
        p."id",
        e."fromId",
        "bucketMonthly"
    ),
    Users AS (
      SELECT 
          p."id" AS "projectId",
          e."fromId" AS "fromId",
          time_bucket(INTERVAL '1 month', e."time") AS "bucketMonthly",
          CASE 
              WHEN SUM(e."amount") >= 1000 THEN 'HIGH_FREQUENCY_USER'
              WHEN SUM(e."amount") >= 10 THEN 'HIGH_VALUE_USER'
              ELSE 'LOW_VALUE_USER'
          END AS "segmentType",
          1 AS amount
      FROM event e
      JOIN project_artifacts_artifact paa ON e."toId" = paa."artifactId"
      JOIN project p ON paa."projectId" = p.id
      JOIN event_type t ON e."typeId" = t.id
      WHERE t."name" = 'CONTRACT_INVOCATION_DAILY_COUNT'
      GROUP BY
        p."id",
        e."fromId",
        "bucketMonthly"
    )
    SELECT
      "projectId",
      "segmentType",
      "bucketMonthly",
      SUM("amount") AS "amount"
    FROM 
      (
          SELECT * FROM Devs
          UNION ALL
          SELECT * FROM Users
      ) combined_data
    GROUP BY
      "projectId",
      "segmentType",
      "bucketMonthly"
    WITH NO DATA;
  `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "users_monthly_to_project",
        'WITH Devs AS (\n      SELECT \n        p."id" AS "projectId",\n        e."fromId" AS "fromId",\n        time_bucket(INTERVAL \'1 month\', e."time") AS "bucketMonthly",\n        CASE \n          WHEN COUNT(DISTINCT CASE WHEN t."name" = \'COMMIT_CODE\' THEN e."time" END) >= 10 THEN \'FULL_TIME_DEV\'\n          WHEN COUNT(DISTINCT CASE WHEN t."name" = \'COMMIT_CODE\' THEN e."time" END) >= 1 THEN \'PART_TIME_DEV\'\n          ELSE \'OTHER_CONTRIBUTOR\'\n        END AS "segmentType",\n        1 AS amount\n      FROM event e\n      JOIN project_artifacts_artifact paa ON e."toId" = paa."artifactId"\n      JOIN project p ON paa."projectId" = p.id        \n      JOIN event_type t ON e."typeId" = t.id\n      WHERE\n        t."name" IN (\n          \'PULL_REQUEST_CREATED\',\n          \'PULL_REQUEST_MERGED\',\n          \'COMMIT_CODE\',\n          \'ISSUE_CLOSED\',\n          \'ISSUE_CREATED\'\n        )\n      GROUP BY\n        p."id",\n        e."fromId",\n        "bucketMonthly"\n    ),\n    Users AS (\n      SELECT \n          p."id" AS "projectId",\n          e."fromId" AS "fromId",\n          time_bucket(INTERVAL \'1 month\', e."time") AS "bucketMonthly",\n          CASE \n              WHEN SUM(e."amount") >= 1000 THEN \'HIGH_FREQUENCY_USER\'\n              WHEN SUM(e."amount") >= 10 THEN \'HIGH_VALUE_USER\'\n              ELSE \'LOW_VALUE_USER\'\n          END AS "segmentType",\n          1 AS amount\n      FROM event e\n      JOIN project_artifacts_artifact paa ON e."toId" = paa."artifactId"\n      JOIN project p ON paa."projectId" = p.id\n      JOIN event_type t ON e."typeId" = t.id\n      WHERE t."name" = \'CONTRACT_INVOCATION_DAILY_COUNT\'\n      GROUP BY\n        p."id",\n        e."fromId",\n        "bucketMonthly"\n    )\n    SELECT\n      "projectId",\n      "segmentType",\n      "bucketMonthly",\n      SUM("amount") AS "amount"\n    FROM \n      (\n          SELECT * FROM Devs\n          UNION ALL\n          SELECT * FROM Users\n      ) combined_data\n    GROUP BY\n      "projectId",\n      "segmentType",\n      "bucketMonthly";',
      ],
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "users_monthly_to_project", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "users_monthly_to_project"`,
    );
  }
}
