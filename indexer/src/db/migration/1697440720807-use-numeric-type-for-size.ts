import { MigrationInterface, QueryRunner } from "typeorm";

export class UseNumericTypeForSize1697440720807 implements MigrationInterface {
  name = "UseNumericTypeForSize1697440720807";

  public async up(queryRunner: QueryRunner): Promise<void> {
    // Add a temp
    await queryRunner.query(
      `ALTER TABLE "event" ADD "size_temp" numeric(78) NOT NULL DEFAULT '0'`,
    );
    // Migrate data to that temp column
    await queryRunner.query(`UPDATE "event" SET "size_temp" = "size"`);

    // Update the column
    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "size"`);
    await queryRunner.query(
      `ALTER TABLE "event" ADD "size" numeric(78) NOT NULL DEFAULT '0'`,
    );

    // Migrate the data to the new column
    await queryRunner.query(`UPDATE "event" SET "size" = "size_temp"`);
    // Drop the data
    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "size_temp"`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Add temp column
    await queryRunner.query(
      `ALTER TABLE "event" ADD "size_temp" bigint NOT NULL DEFAULT '0'`,
    );
    // This has data loss during a rollback
    await queryRunner.query(
      `UPDATE "event" SET "size_temp" = "size" where "size" < 9223372036854775807`,
    );

    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "size"`);
    await queryRunner.query(
      `ALTER TABLE "event" ADD "size" bigint NOT NULL DEFAULT '0'`,
    );

    // Migrate the data to the new column
    await queryRunner.query(`UPDATE "event" SET "size" = "size_temp"`);
    // Drop the data
    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "size_temp"`);
  }
}
