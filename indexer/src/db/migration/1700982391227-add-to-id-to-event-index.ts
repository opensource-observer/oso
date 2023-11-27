import { MigrationInterface, QueryRunner } from "typeorm";

export class AddToIdToEventIndex1700982391227 implements MigrationInterface {
  name = "AddToIdToEventIndex1700982391227";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1bbe6d5332074e612550af9f35"`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_0b427e8ea6458c4a6a64212ce1" ON "event" ("sourceId", "typeId", "toId", "time") `,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_0b427e8ea6458c4a6a64212ce1"`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1bbe6d5332074e612550af9f35" ON "event" ("sourceId", "time", "typeId") `,
    );
  }
}
