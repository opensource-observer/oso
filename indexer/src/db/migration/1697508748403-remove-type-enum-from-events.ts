import { MigrationInterface, QueryRunner } from "typeorm";

export class RemoveTypeEnumFromEvents1697508748403
  implements MigrationInterface
{
  name = "RemoveTypeEnumFromEvents1697508748403";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_7ea8a55b1ae8ec8d4a5e0af3e5"`,
    );
    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "type"`);
    await queryRunner.query(`DROP TYPE "public"."event_type_enum"`);
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1bbe6d5332074e612550af9f35" ON "event" ("typeId", "sourceId", "time") `,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1bbe6d5332074e612550af9f35"`,
    );
    await queryRunner.query(
      `CREATE TYPE "public"."event_type_enum" AS ENUM('COMMIT_CODE', 'CONTRACT_INVOKED', 'CONTRACT_INVOKED_AGGREGATE_STATS', 'DOWNLOADS', 'DOWNSTREAM_DEPENDENCY_COUNT', 'FORKED', 'FORK_AGGREGATE_STATS', 'FUNDING', 'ISSUE_CLOSED', 'ISSUE_CREATED', 'ISSUE_FILED', 'ISSUE_REMOVED_FROM_PROJECT', 'ISSUE_REOPENED', 'PULL_REQUEST_APPROVED', 'PULL_REQUEST_CLOSED', 'PULL_REQUEST_CREATED', 'PULL_REQUEST_MERGED', 'PULL_REQUEST_REMOVED_FROM_PROJECT', 'PULL_REQUEST_REOPENED', 'STARRED', 'STAR_AGGREGATE_STATS', 'UPSTREAM_DEPENDENCY_COUNT', 'USERS_INTERACTED', 'WATCHER_AGGREGATE_STATS')`,
    );
    // Set a default so the rollback can succeed. We will need to do a custom
    // query to fix it if necessary.
    await queryRunner.query(
      `ALTER TABLE "event" ADD "type" "public"."event_type_enum" NOT NULL DEFAULT 'COMMIT_CODE'`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_7ea8a55b1ae8ec8d4a5e0af3e5" ON "event" ("sourceId", "time", "type") `,
    );
  }
}
