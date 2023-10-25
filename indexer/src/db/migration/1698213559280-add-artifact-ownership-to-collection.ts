import { MigrationInterface, QueryRunner } from "typeorm";

export class AddArtifactOwnershipToCollection1698213559280
  implements MigrationInterface
{
  name = "AddArtifactOwnershipToCollection1698213559280";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE "collection" ADD "ownerId" integer`);
    await queryRunner.query(
      `ALTER TABLE "collection" ADD CONSTRAINT "FK_71af9149c567d79c9532f7e47d0" FOREIGN KEY ("ownerId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "collection" DROP CONSTRAINT "FK_71af9149c567d79c9532f7e47d0"`,
    );
    await queryRunner.query(`ALTER TABLE "collection" DROP COLUMN "ownerId"`);
  }
}
