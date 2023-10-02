import { MigrationInterface, QueryRunner } from "typeorm";

export class JobExecutionVersion1696246784819 implements MigrationInterface {
  name = "JobExecutionVersion1696246784819";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "job_execution" ADD "version" integer NOT NULL DEFAULT '0'`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "job_execution" DROP COLUMN "version"`,
    );
  }
}
