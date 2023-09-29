import { MigrationInterface, QueryRunner } from "typeorm";

export class UpdateJob1696000344339 implements MigrationInterface {
  name = "UpdateJob1696000344339";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE "job_group_lock" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "name" text NOT NULL, CONSTRAINT "PK_7ac2c36fc088312e6aa48757bea" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_e2e4d62585b211a9ce3e53a940" ON "job_group_lock" ("name") `,
    );
    await queryRunner.query(`ALTER TABLE "job" DROP COLUMN "execGroup"`);
    await queryRunner.query(`ALTER TABLE "job" ADD "group" text`);
    await queryRunner.query(
      `ALTER TABLE "job" ADD "options" jsonb NOT NULL DEFAULT '{}'`,
    );
    await queryRunner.query(
      `ALTER TABLE "job_execution" ADD "attempt" integer NOT NULL`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_93b37df8fba4d12188e1a2fa60" ON "job" ("scheduledTime", "collector") `,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_e11d88cacc0910d13d258ebe5a" ON "job_execution" ("jobId", "attempt") `,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_e11d88cacc0910d13d258ebe5a"`,
    );
    await queryRunner.query(
      `DROP INDEX "public"."IDX_93b37df8fba4d12188e1a2fa60"`,
    );
    await queryRunner.query(
      `ALTER TABLE "job_execution" DROP COLUMN "attempt"`,
    );
    await queryRunner.query(`ALTER TABLE "job" DROP COLUMN "options"`);
    await queryRunner.query(`ALTER TABLE "job" DROP COLUMN "group"`);
    await queryRunner.query(`ALTER TABLE "job" ADD "execGroup" text NOT NULL`);
    await queryRunner.query(
      `DROP INDEX "public"."IDX_e2e4d62585b211a9ce3e53a940"`,
    );
    await queryRunner.query(`DROP TABLE "job_group_lock"`);
  }
}
