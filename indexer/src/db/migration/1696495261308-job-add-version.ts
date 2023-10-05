import { MigrationInterface, QueryRunner } from "typeorm";

export class JobAddVersion1696495261308 implements MigrationInterface {
  name = "JobAddVersion1696495261308";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "job" ADD "version" integer NOT NULL`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "job" DROP COLUMN "version"`);
  }
}
