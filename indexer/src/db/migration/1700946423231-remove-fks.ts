import { MigrationInterface, QueryRunner } from "typeorm";

export class RemoveFks1700946423231 implements MigrationInterface {
  name = "RemoveFks1700946423231";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "event" DROP CONSTRAINT "FK_255cc0faa667931c91431716165"`,
    );
    await queryRunner.query(
      `ALTER TABLE "event" DROP CONSTRAINT "FK_404b3d263eafc41aae2044e9b85"`,
    );
    await queryRunner.query(
      `ALTER TABLE "event" DROP CONSTRAINT "FK_b36ab188856dd8cf3d6c7ec4f48"`,
    );
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1bbe6d5332074e612550af9f35"`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" ADD "toId" integer`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" ADD "fromId" integer`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" ALTER COLUMN "toName" DROP NOT NULL`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" ALTER COLUMN "toNamespace" DROP NOT NULL`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" ALTER COLUMN "toType" DROP NOT NULL`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" ALTER COLUMN "toType" SET NOT NULL`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" ALTER COLUMN "toNamespace" SET NOT NULL`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" ALTER COLUMN "toName" SET NOT NULL`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" DROP COLUMN "fromId"`,
    );
    await queryRunner.query(
      `ALTER TABLE "recorder_temp_event" DROP COLUMN "toId"`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1bbe6d5332074e612550af9f35" ON "event" ("sourceId", "time", "typeId") `,
    );
    await queryRunner.query(
      `ALTER TABLE "event" ADD CONSTRAINT "FK_b36ab188856dd8cf3d6c7ec4f48" FOREIGN KEY ("fromId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "event" ADD CONSTRAINT "FK_404b3d263eafc41aae2044e9b85" FOREIGN KEY ("toId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "event" ADD CONSTRAINT "FK_255cc0faa667931c91431716165" FOREIGN KEY ("typeId") REFERENCES "event_type"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
  }
}
