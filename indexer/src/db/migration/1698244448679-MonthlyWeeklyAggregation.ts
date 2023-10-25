import { MigrationInterface, QueryRunner } from "typeorm";

export class MonthlyWeeklyAggregation1698244448679
  implements MigrationInterface
{
  name = "MonthlyWeeklyAggregation1698244448679";

  public async up(queryRunner: QueryRunner): Promise<void> {
    // Add views
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_daily_to_artifact"
      WITH (timescaledb.continuous)
      AS SELECT "toId" AS "artifactId",
        "typeId",
        time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
        SUM(amount) as "amount"
      FROM "event" 
      GROUP BY "artifactId", "typeId", "bucketDaily"
      WITH NO DATA;
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_daily_to_artifact",
        'SELECT "toId" AS "artifact",\n      "typeId",\n      time_bucket(INTERVAL \'1 day\', "time") AS "bucketDaily",\n      SUM(amount) as "amount"\n    FROM "event" \n    GROUP BY "toId", "typeId", "bucketDaily"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_weekly_to_artifact"
      WITH (timescaledb.continuous)
      AS SELECT "artifactId",
        "typeId",
        time_bucket(INTERVAL '1 week', "bucketDaily") AS "bucketWeekly",
        SUM(amount) as "amount"
      FROM "events_daily_to_artifact" 
      GROUP BY "artifactId", "typeId", "bucketWeekly"
      WITH NO DATA;
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_weekly_to_artifact",
        'SELECT "artifactId",\n      "typeId",\n      time_bucket(INTERVAL \'1 week\', "bucketDaily") AS "bucketWeekly",\n      SUM(amount) as "amount"\n    FROM "events_daily_by_artifact" \n    GROUP BY "toId", "typeId", "bucketWeekly"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_monthly_to_artifact"
      WITH (timescaledb.continuous)
      AS SELECT "artifactId",
        "typeId",
        time_bucket(INTERVAL '1 month', "bucketDaily") AS "bucketMonthly",
        SUM(amount) as "amount"
      FROM "events_daily_to_artifact" 
      GROUP BY "artifactId", "typeId", "bucketMonthly"
      WITH NO DATA;
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_monthly_to_artifact",
        'SELECT "artifactId",\n      "typeId",\n      time_bucket(INTERVAL \'1 month\', "bucketDaily") AS "bucketMonthly",\n      SUM(amount) as "amount"\n    FROM "events_daily_by_artifact" \n    GROUP BY "toId", "typeId", "bucketMonthly"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_daily_to_project"
      WITH (timescaledb.continuous)
      AS SELECT "projectId",
        "typeId",
        time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
        SUM(amount) as "amount"
      FROM "event"
      INNER JOIN "project_artifacts_artifact"
        on "project_artifacts_artifact"."artifactId" = "event"."toId"
      GROUP BY "projectId", "typeId", "bucketDaily"
      WITH NO DATA;
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_daily_to_project",
        'SELECT "projectId",\n      "typeId",\n      time_bucket(INTERVAL \'1 day\', "time") AS "bucketDaily",\n      SUM(amount) as "amount"\n    FROM "event"\n    INNER JOIN "project_artifacts_artifact"\n      on "project_artifacts_artifact"."artifactId" = "event"."toId"\n    GROUP BY "projectId", "typeId", "bucketDaily"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_weekly_to_project"
      WITH (timescaledb.continuous)
      AS SELECT "projectId",
        "typeId",
        time_bucket(INTERVAL '1 week', "bucketDaily") AS "bucketWeekly",
        SUM(amount) as "amount"
      FROM "events_daily_to_project" 
      GROUP BY "projectId", "typeId", "bucketWeekly"
      WITH NO DATA;
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_weekly_to_project",
        'SELECT "projectId",\n      "typeId",\n      time_bucket(INTERVAL \'1 week\', "bucketDaily") AS "bucketWeekly",\n      SUM(amount) as "amount"\n    FROM "events_daily_by_project" \n    GROUP BY "toId", "typeId", "bucketWeekly"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_monthly_to_project"
      WITH (timescaledb.continuous)
      AS SELECT "projectId",
        "typeId",
        time_bucket(INTERVAL '1 month', "bucketDaily") AS "bucketMonthly",
        SUM(amount) as "amount"
      FROM "events_daily_to_project" 
      GROUP BY "projectId", "typeId", "bucketMonthly"
      WITH NO DATA;
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_monthly_to_project",
        'SELECT "projectId",\n      "typeId",\n      time_bucket(INTERVAL \'1 month\', "bucketDaily") AS "bucketMonthly",\n      SUM(amount) as "amount"\n    FROM "events_daily_by_project" \n    GROUP BY "toId", "typeId", "bucketMonthly"\n    WITH NO DATA;',
      ],
    );

    // Add refresh policies
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_daily_to_artifact', start_offset => INTERVAL '1 month', end_offset => INTERVAL '1 day', schedule_interval => INTERVAL '1 hour');`,
    );
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_weekly_to_artifact', start_offset => INTERVAL '6 month', end_offset => INTERVAL '1 week', schedule_interval => INTERVAL '1 day');`,
    );
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_monthly_to_artifact', start_offset => INTERVAL '1 year', end_offset => INTERVAL '1 month', schedule_interval => INTERVAL '1 week');`,
    );
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_daily_to_project', start_offset => INTERVAL '1 month', end_offset => INTERVAL '1 day', schedule_interval => INTERVAL '1 hour');`,
    );
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_weekly_to_project', start_offset => INTERVAL '6 month', end_offset => INTERVAL '1 week', schedule_interval => INTERVAL '1 day');`,
    );
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_monthly_to_project', start_offset => INTERVAL '1 year', end_offset => INTERVAL '1 month', schedule_interval => INTERVAL '1 week');`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Remove refresh policies
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_monthly_to_project');`,
    );
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_weekly_to_project');`,
    );
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_daily_to_project');`,
    );
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_monthly_to_artifact');`,
    );
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_weekly_to_artifact');`,
    );
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_daily_to_artifact');`,
    );

    // Remove views
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_monthly_to_project", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_monthly_to_project"`,
    );
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_weekly_to_project", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_weekly_to_project"`,
    );
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_daily_to_project", "public"],
    );
    await queryRunner.query(`DROP MATERIALIZED VIEW "events_daily_to_project"`);
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_monthly_to_artifact", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_monthly_to_artifact"`,
    );
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_weekly_to_artifact", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_weekly_to_artifact"`,
    );
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_daily_to_artifact", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_daily_to_artifact"`,
    );
  }
}
