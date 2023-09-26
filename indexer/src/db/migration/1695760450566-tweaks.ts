import { MigrationInterface, QueryRunner } from "typeorm";

export class Tweaks1695760450566 implements MigrationInterface {
  name = "Tweaks1695760450566";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1b59a64c744d72143d2b96b2c7"`,
    );
    await queryRunner.query(
      `ALTER TYPE "public"."artifact_namespace_enum" RENAME TO "artifact_namespace_enum_old"`,
    );
    await queryRunner.query(
      `CREATE TYPE "public"."artifact_namespace_enum" AS ENUM('ethereum', 'optimism', 'goerli', 'github', 'gitlab', 'npm')`,
    );
    await queryRunner.query(
      `ALTER TABLE "artifact" ALTER COLUMN "namespace" TYPE "public"."artifact_namespace_enum" USING "namespace"::"text"::"public"."artifact_namespace_enum"`,
    );
    await queryRunner.query(`DROP TYPE "public"."artifact_namespace_enum_old"`);
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1b59a64c744d72143d2b96b2c7" ON "artifact" ("namespace", "name") `,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1b59a64c744d72143d2b96b2c7"`,
    );
    await queryRunner.query(
      `CREATE TYPE "public"."artifact_namespace_enum_old" AS ENUM('NPM_REGISTRY', 'ethereum', 'github', 'gitlab', 'goerli', 'optimism')`,
    );
    await queryRunner.query(
      `ALTER TABLE "artifact" ALTER COLUMN "namespace" TYPE "public"."artifact_namespace_enum_old" USING "namespace"::"text"::"public"."artifact_namespace_enum_old"`,
    );
    await queryRunner.query(`DROP TYPE "public"."artifact_namespace_enum"`);
    await queryRunner.query(
      `ALTER TYPE "public"."artifact_namespace_enum_old" RENAME TO "artifact_namespace_enum"`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1b59a64c744d72143d2b96b2c7" ON "artifact" ("namespace", "name") `,
    );
  }
}
