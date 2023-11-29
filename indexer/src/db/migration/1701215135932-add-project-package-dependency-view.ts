import { MigrationInterface, QueryRunner } from "typeorm";

export class AddProjectPackageDependencyView1701215135932
  implements MigrationInterface
{
  name = "AddProjectPackageDependencyView1701215135932";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE VIEW "project_package_dependency" AS 
    SELECT 
      paa_r."projectId" as "dependentProjectId",
      "repoId" as "dependentRepoId",
      paa_d."projectId" as "dependencyProjectId",
      rd."dependencyId" as "dependencyId"
    FROM "repo_dependency" rd
    INNER JOIN "project_artifacts_artifact" paa_r
      on "paa_r"."artifactId" = rd."repoId"
    LEFT OUTER JOIN "project_artifacts_artifact" paa_d
      on "paa_d"."artifactId" = rd."dependencyId"
  `);
    await queryRunner.query(
      `INSERT INTO "typeorm_metadata"("database", "schema", "table", "type", "name", "value") VALUES (DEFAULT, $1, DEFAULT, $2, $3, $4)`,
      [
        "public",
        "VIEW",
        "project_package_dependency",
        'SELECT \n      paa_r."projectId" as "dependentProjectId",\n      "repoId" as "dependentRepoId",\n      paa_d."projectId" as "dependencyProjectId",\n      rd."dependencyId" as "dependencyId"\n    FROM "repo_dependency" rd\n    INNER JOIN "project_artifacts_artifact" paa_r\n      on "paa_r"."artifactId" = rd."repoId"\n    LEFT OUTER JOIN "project_artifacts_artifact" paa_d\n      on "paa_d"."artifactId" = rd."dependencyId"',
      ],
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `DELETE FROM "typeorm_metadata" WHERE "type" = $1 AND "name" = $2 AND "schema" = $3`,
      ["VIEW", "project_package_dependency", "public"],
    );
    await queryRunner.query(`DROP VIEW "project_package_dependency"`);
  }
}
