import { MigrationInterface, QueryRunner } from "typeorm";

export class AddScheduleType1698573838734 implements MigrationInterface {
  name = "AddScheduleType1698573838734";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_93b37df8fba4d12188e1a2fa60"`,
    );
    await queryRunner.query(
      `ALTER TABLE "job" ADD "scheduleType" text NOT NULL DEFAULT 'main'`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1aa59c02d7f21ade4eafd273d1" ON "job" ("scheduledTime", "scheduleType", "collector") `,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1aa59c02d7f21ade4eafd273d1"`,
    );
    await queryRunner.query(`ALTER TABLE "job" DROP COLUMN "scheduleType"`);
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_93b37df8fba4d12188e1a2fa60" ON "job" ("scheduledTime", "collector") `,
    );
  }
}
