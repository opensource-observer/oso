import { MigrationInterface, QueryRunner } from "typeorm";

export class RebuildViews1697488360710 implements MigrationInterface {
  name = "RebuildViews1697488360710";

  public async up(queryRunner: QueryRunner): Promise<void> {
    // Delete the original views
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_daily_by_project", "public"],
    );
    await queryRunner.query(`
      SELECT remove_continuous_aggregate_policy('events_daily_by_project');
    `);
    await queryRunner.query(`DROP MATERIALIZED VIEW "events_daily_by_project"`);
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_daily_by_artifact", "public"],
    );
    await queryRunner.query(`
      SELECT remove_continuous_aggregate_policy('events_daily_by_artifact');
    `);
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_daily_by_artifact"`,
    );

    // Create using typeId
    await queryRunner.query(`
      CREATE MATERIALIZED VIEW "events_daily_by_artifact" WITH (timescaledb.continuous) AS 
      SELECT "toId",
        "typeId",
        time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
        SUM(amount) as "amount"
      FROM "event" 
      GROUP BY "toId", "typeId", "bucketDaily"
      WITH NO DATA;
    `);
    await queryRunner.query(`
      SELECT add_continuous_aggregate_policy('events_daily_by_artifact',
        start_offset => INTERVAL '1 month',
        end_offset => INTERVAL '1 day',
        schedule_interval => INTERVAL '1 hour');
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_daily_by_artifact",
        'SELECT "toId",\n      "typeId",\n      time_bucket(INTERVAL \'1 day\', "time") AS "bucketDaily",\n      SUM(amount) as "amount"\n    FROM "event" \n    GROUP BY "toId", "typeId", "bucketDaily"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`
      CREATE MATERIALIZED VIEW "events_daily_by_project" WITH (timescaledb.continuous) AS 
      SELECT "projectId",
        "typeId",
        time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
        SUM(amount) as "amount"
      FROM "event"
      INNER JOIN "project_artifacts_artifact"
        on "project_artifacts_artifact"."artifactId" = "event"."toId"
      GROUP BY "projectId", "typeId", "bucketDaily"
      WITH NO DATA;
    `);
    await queryRunner.query(`
      SELECT add_continuous_aggregate_policy('events_daily_by_project',
        start_offset => INTERVAL '1 month',
        end_offset => INTERVAL '1 day',
        schedule_interval => INTERVAL '1 hour');
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_daily_by_project",
        'SELECT "projectId",\n      "typeId",\n      time_bucket(INTERVAL \'1 day\', "time") AS "bucketDaily",\n      SUM(amount) as "amount"\n    FROM "event"\n    INNER JOIN "project_artifacts_artifact"\n      on "project_artifacts_artifact"."artifactId" = "event"."toId"\n    GROUP BY "projectId", "typeId", "bucketDaily"\n    WITH NO DATA;',
      ],
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Delete the new views
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_daily_by_project", "public"],
    );
    await queryRunner.query(`
      SELECT remove_continuous_aggregate_policy('events_daily_by_project');
    `);
    await queryRunner.query(`DROP MATERIALIZED VIEW "events_daily_by_project"`);
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_daily_by_artifact", "public"],
    );
    await queryRunner.query(`
      SELECT remove_continuous_aggregate_policy('events_daily_by_artifact');
    `);
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_daily_by_artifact"`,
    );

    // Recreate the old views
    await queryRunner.query(`
      CREATE MATERIALIZED VIEW "events_daily_by_artifact" WITH (timescaledb.continuous) AS 
      SELECT "toId",
        "type",
        time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
        SUM(amount) as "amount"
      FROM "event" 
      GROUP BY "toId", "type", "bucketDaily"
      WITH NO DATA;
    `);
    await queryRunner.query(`
      SELECT add_continuous_aggregate_policy('events_daily_by_artifact',
        start_offset => INTERVAL '1 month',
        end_offset => INTERVAL '1 day',
        schedule_interval => INTERVAL '1 hour');
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_daily_by_artifact",
        'SELECT "toId",\n      "type",\n      time_bucket(INTERVAL \'1 day\', "time") AS "bucketDaily",\n      SUM(amount) as "amount"\n    FROM "event" \n    GROUP BY "toId", "type", "bucketDaily"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`
      CREATE MATERIALIZED VIEW "events_daily_by_project" WITH (timescaledb.continuous) AS 
      SELECT "projectId",
        "type",
        time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
        SUM(amount) as "amount"
      FROM "event"
      INNER JOIN "project_artifacts_artifact"
        on "project_artifacts_artifact"."artifactId" = "event"."toId"
      GROUP BY "projectId", "type", "bucketDaily"
      WITH NO DATA;
    `);
    await queryRunner.query(`
      SELECT add_continuous_aggregate_policy('events_daily_by_project',
        start_offset => INTERVAL '1 month',
        end_offset => INTERVAL '1 day',
        schedule_interval => INTERVAL '1 hour');
    `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_daily_by_project",
        'SELECT "projectId",\n      "type",\n      time_bucket(INTERVAL \'1 day\', "time") AS "bucketDaily",\n      SUM(amount) as "amount"\n    FROM "event"\n    INNER JOIN "project_artifacts_artifact"\n      on "project_artifacts_artifact"."artifactId" = "event"."toId"\n    GROUP BY "projectId", "type", "bucketDaily"\n    WITH NO DATA;',
      ],
    );
  }
}
