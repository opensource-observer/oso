import { MigrationInterface, QueryRunner } from "typeorm";

export class JobAddVersion1696495364452 implements MigrationInterface {
  name = "JobAddVersion1696495364452";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "job" ADD "version" integer NOT NULL DEFAULT '0'`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "job" DROP COLUMN "version"`);
  }
}
