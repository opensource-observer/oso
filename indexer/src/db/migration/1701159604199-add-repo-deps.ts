import { MigrationInterface, QueryRunner } from "typeorm";

export class AddRepoDeps1701159604199 implements MigrationInterface {
  name = "AddRepoDeps1701159604199";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE "repo_dependency" ("id" SERIAL NOT NULL, "repoId" integer, "dependencyId" integer, CONSTRAINT "PK_b0be9917812af14b5aa86eaa7e6" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `ALTER TABLE "repo_dependency" ADD CONSTRAINT "FK_f04c98d3fe037b1e900b15c2dd2" FOREIGN KEY ("repoId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "repo_dependency" ADD CONSTRAINT "FK_c6410ea255899b5c189297031fc" FOREIGN KEY ("dependencyId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "repo_dependency" DROP CONSTRAINT "FK_c6410ea255899b5c189297031fc"`,
    );
    await queryRunner.query(
      `ALTER TABLE "repo_dependency" DROP CONSTRAINT "FK_f04c98d3fe037b1e900b15c2dd2"`,
    );
    await queryRunner.query(`DROP TABLE "repo_dependency"`);
  }
}
