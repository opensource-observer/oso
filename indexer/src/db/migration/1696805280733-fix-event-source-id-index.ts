import { MigrationInterface, QueryRunner } from "typeorm";

export class FixEventSourceIdIndex1696805280733 implements MigrationInterface {
  name = "FixEventSourceIdIndex1696805280733";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_8eb34e6d33033e17e91776c1c2"`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_7ea8a55b1ae8ec8d4a5e0af3e5" ON "event" ("type", "sourceId", "time") `,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_7ea8a55b1ae8ec8d4a5e0af3e5"`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_8eb34e6d33033e17e91776c1c2" ON "event" ("sourceId", "time") `,
    );
  }
}
