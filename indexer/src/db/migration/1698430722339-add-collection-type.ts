import { MigrationInterface, QueryRunner } from "typeorm";

export class AddCollectionType1698430722339 implements MigrationInterface {
  name = "AddCollectionType1698430722339";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE "collection_type" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "name" text NOT NULL, CONSTRAINT "PK_75c673f46e25c52205fae22130c" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_7be682a45f3aabbd9a662cd38c" ON "collection_type" ("name") `,
    );

    // Load initial values into the collection_type table
    const collectionTypes = [
      "OSS_DIRECTORY",
      "ARTIFACT_DEPENDENCIES",
      "ARTIFACT_DEPENDENTS",
      "USER",
    ];

    // Initialize the event type table. Not worrying about sql injection
    // here. We're the ones providing input.
    await queryRunner.query(
      `
      INSERT INTO collection_type(name)
      SELECT UNNEST($1::text[])
    `,
      [collectionTypes],
    );

    await queryRunner.query(`ALTER TABLE "collection" ADD "typeId" integer`);
    await queryRunner.query(
      `ALTER TABLE "collection" ADD CONSTRAINT "FK_59018e4fc204e8ab8e76bd8005a" FOREIGN KEY ("typeId") REFERENCES "collection_type"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );

    // Update all existing collections to use `OSS_DIRECTORY` at the time of
    // migration this was the only kind of collection
    await queryRunner.query(
      `
      UPDATE collection
      SET "typeId"=1
      `,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "collection" DROP CONSTRAINT "FK_59018e4fc204e8ab8e76bd8005a"`,
    );
    await queryRunner.query(`ALTER TABLE "collection" DROP COLUMN "typeId"`);
    await queryRunner.query(
      `DROP INDEX "public"."IDX_7be682a45f3aabbd9a662cd38c"`,
    );
    await queryRunner.query(`DROP TABLE "collection_type"`);
  }
}
