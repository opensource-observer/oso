import { MigrationInterface, QueryRunner } from "typeorm";

export class EventsToCollection1699775810960 implements MigrationInterface {
  name = "EventsToCollection1699775810960";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_daily_to_collection"
      WITH (timescaledb.continuous)
    AS SELECT "collectionId",
      "typeId",
      time_bucket(INTERVAL '1 day', "bucketDaily") AS "bucketDay",
      SUM(amount) as "amount"
    FROM "events_daily_to_project"
    INNER JOIN "collection_projects_project"
      ON "collection_projects_project"."projectId" = "events_daily_to_project"."projectId"
    GROUP BY "collectionId", "typeId", "bucketDay"
    WITH NO DATA;
  `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_daily_to_collection",
        'SELECT "collectionId",\n      "typeId",\n      time_bucket(INTERVAL \'1 day\', "bucketDaily") AS "bucketDay",\n      SUM(amount) as "amount"\n    FROM "events_daily_to_project"\n    INNER JOIN "collection_projects_project"\n      ON "collection_projects_project"."projectId" = "events_daily_to_project"."projectId"\n    GROUP BY "collectionId", "typeId", "bucketDay"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_weekly_to_collection"
      WITH (timescaledb.continuous)
    AS SELECT "collectionId",
      "typeId",
      time_bucket(INTERVAL '1 week', "bucketDay") AS "bucketWeekly",
      SUM(amount) as "amount"
    FROM "events_daily_to_collection" 
    GROUP BY "collectionId", "typeId", "bucketWeekly"
    WITH NO DATA;
  `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_weekly_to_collection",
        'SELECT "collectionId",\n      "typeId",\n      time_bucket(INTERVAL \'1 week\', "bucketDay") AS "bucketWeekly",\n      SUM(amount) as "amount"\n    FROM "events_daily_to_collection" \n    GROUP BY "collectionId", "typeId", "bucketWeekly"\n    WITH NO DATA;',
      ],
    );
    await queryRunner.query(`CREATE MATERIALIZED VIEW "events_monthly_to_collection"
      WITH (timescaledb.continuous)
    AS SELECT "collectionId",
      "typeId",
      time_bucket(INTERVAL '1 month', "bucketDay") AS "bucketMonthly",
      SUM(amount) as "amount"
    FROM "events_daily_to_collection" 
    GROUP BY "collectionId", "typeId", "bucketMonthly"
    WITH NO DATA;
  `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "MATERIALIZED_VIEW",
        "events_monthly_to_collection",
        'SELECT "collectionId",\n      "typeId",\n      time_bucket(INTERVAL \'1 month\', "bucketDay") AS "bucketMonthly",\n      SUM(amount) as "amount"\n    FROM "events_daily_to_collection" \n    GROUP BY "collectionId", "typeId", "bucketMonthly"\n    WITH NO DATA;',
      ],
    );

    // Add refresh policies
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_daily_to_collection', start_offset => INTERVAL '1 month', end_offset => INTERVAL '1 day', schedule_interval => INTERVAL '1 hour');`,
    );
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_weekly_to_collection', start_offset => INTERVAL '6 month', end_offset => INTERVAL '1 week', schedule_interval => INTERVAL '1 day');`,
    );
    await queryRunner.query(
      `SELECT add_continuous_aggregate_policy('events_monthly_to_collection', start_offset => INTERVAL '1 year', end_offset => INTERVAL '1 month', schedule_interval => INTERVAL '1 week');`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Remove refresh policies
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_monthly_to_collection');`,
    );
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_weekly_to_collection');`,
    );
    await queryRunner.query(
      `SELECT remove_continuous_aggregate_policy('events_daily_to_collection');`,
    );

    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_monthly_to_collection", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_monthly_to_collection"`,
    );
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_weekly_to_collection", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_weekly_to_collection"`,
    );
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["MATERIALIZED_VIEW", "events_daily_to_collection", "public"],
    );
    await queryRunner.query(
      `DROP MATERIALIZED VIEW "events_daily_to_collection"`,
    );
  }
}
