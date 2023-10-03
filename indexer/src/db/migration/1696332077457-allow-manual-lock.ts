import { MigrationInterface, QueryRunner } from "typeorm";

export class AllowManualLock1696332077457 implements MigrationInterface {
  name = "AllowManualLock1696332077457";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TYPE "public"."job_status_enum" RENAME TO "job_status_enum_old"`,
    );
    await queryRunner.query(
      `CREATE TYPE "public"."job_status_enum" AS ENUM('PENDING', 'COMPLETE', 'MANUALLY_LOCKED')`,
    );
    await queryRunner.query(
      `ALTER TABLE "job" ALTER COLUMN "status" TYPE "public"."job_status_enum" USING "status"::"text"::"public"."job_status_enum"`,
    );
    await queryRunner.query(`DROP TYPE "public"."job_status_enum_old"`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TYPE "public"."job_status_enum_old" AS ENUM('PENDING', 'COMPLETE')`,
    );
    await queryRunner.query(
      `ALTER TABLE "job" ALTER COLUMN "status" TYPE "public"."job_status_enum_old" USING "status"::"text"::"public"."job_status_enum_old"`,
    );
    await queryRunner.query(`DROP TYPE "public"."job_status_enum"`);
    await queryRunner.query(
      `ALTER TYPE "public"."job_status_enum_old" RENAME TO "job_status_enum"`,
    );
  }
}
