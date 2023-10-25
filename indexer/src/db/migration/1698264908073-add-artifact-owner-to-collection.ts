import { MigrationInterface, QueryRunner } from "typeorm";

export class AddArtifactOwnerToCollection1698264908073
  implements MigrationInterface
{
  name = "AddArtifactOwnerToCollection1698264908073";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "collection" ADD "artifactOwnerId" integer`,
    );
    await queryRunner.query(
      `ALTER TABLE "collection" ADD CONSTRAINT "FK_e5cf4e13b16b587a9ca6a12d721" FOREIGN KEY ("artifactOwnerId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "collection" DROP CONSTRAINT "FK_e5cf4e13b16b587a9ca6a12d721"`,
    );
    await queryRunner.query(
      `ALTER TABLE "collection" DROP COLUMN "artifactOwnerId"`,
    );
  }
}
