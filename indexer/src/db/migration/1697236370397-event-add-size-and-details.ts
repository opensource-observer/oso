import { MigrationInterface, QueryRunner } from "typeorm";

export class EventAddSizeAndDetails1697236370397 implements MigrationInterface {
  name = "EventAddSizeAndDetails1697236370397";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "event" ADD "size" bigint NOT NULL DEFAULT '0'`,
    );
    await queryRunner.query(
      `ALTER TABLE "event" ADD "details" jsonb NOT NULL DEFAULT '{}'`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "details"`);
    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "size"`);
  }
}
