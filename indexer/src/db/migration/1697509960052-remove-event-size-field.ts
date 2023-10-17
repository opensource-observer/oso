import { MigrationInterface, QueryRunner } from "typeorm";

export class RemoveEventSizeField1697509960052 implements MigrationInterface {
  name = "RemoveEventSizeField1697509960052";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "size"`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "event" ADD "size" bigint NOT NULL DEFAULT '0'`,
    );
  }
}
