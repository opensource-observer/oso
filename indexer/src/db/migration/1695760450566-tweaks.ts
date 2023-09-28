import { MigrationInterface, QueryRunner } from "typeorm";

export class Tweaks1695760450566 implements MigrationInterface {
  name = "Tweaks1695760450566";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1b59a64c744d72143d2b96b2c7"`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1b59a64c744d72143d2b96b2c7" ON "artifact" ("namespace", "name") `,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1b59a64c744d72143d2b96b2c7"`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1b59a64c744d72143d2b96b2c7" ON "artifact" ("namespace", "name") `,
    );
  }
}
