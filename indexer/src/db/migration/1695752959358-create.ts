import { MigrationInterface, QueryRunner } from "typeorm";

export class Create1695752959358 implements MigrationInterface {
  name = "Create1695752959358";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TYPE "public"."artifact_type_enum" AS ENUM('eoa_address', 'safe_address', 'contract_address', 'factory_address', 'git_repository', 'git_email', 'git_name', 'github_org', 'github_user', 'npm_package')`,
    );
    await queryRunner.query(
      `CREATE TYPE "public"."artifact_namespace_enum" AS ENUM('ethereum', 'optimism', 'goerli', 'github', 'gitlab', 'npm')`,
    );
    await queryRunner.query(
      `CREATE TYPE "public"."event_type_enum" AS ENUM('funding', 'pull_request_created', 'pull_request_merged', 'commit_code', 'issue_filed', 'issue_closed', 'downstream_dependency_count', 'upstream_dependency_count', 'downloads', 'contract_invoked', 'users_interacted', 'contract_invoked_aggregate_stats', 'pull_request_closed', 'star_aggregate_stats', 'pull_request_reopened', 'pull_request_removed_from_project', 'pull_request_approved', 'issue_created', 'issue_reopened', 'issue_removed_from_project', 'starred', 'fork_aggregate_stats', 'forked', 'watcher_aggregate_stats')`,
    );
    await queryRunner.query(
      `CREATE TYPE "public"."job_status_enum" AS ENUM('pending', 'complete')`,
    );
    await queryRunner.query(
      `CREATE TYPE "public"."job_execution_status_enum" AS ENUM('active', 'complete', 'failed')`,
    );
    await queryRunner.query(
      `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE`,
    );
    await queryRunner.query(
      `CREATE TABLE "collection" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "name" text NOT NULL, "description" text, "verified" boolean NOT NULL DEFAULT false, "slug" text NOT NULL, CONSTRAINT "UQ_75a6fd6eedd7fa7378de400b0aa" UNIQUE ("slug"), CONSTRAINT "PK_ad3f485bbc99d875491f44d7c85" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE TABLE "project" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "name" text NOT NULL, "description" text, "verified" boolean NOT NULL DEFAULT false, "slug" text NOT NULL, CONSTRAINT "UQ_6fce32ddd71197807027be6ad38" UNIQUE ("slug"), CONSTRAINT "PK_4d68b1358bb5b766d3e78f32f57" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE TABLE "artifact" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "type" "public"."artifact_type_enum" NOT NULL, "namespace" "public"."artifact_namespace_enum" NOT NULL, "name" text NOT NULL, "url" text, CONSTRAINT "PK_1f238d1d4ef8f85d0c0b8616fa3" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_1b59a64c744d72143d2b96b2c7" ON "artifact" ("namespace", "name") `,
    );
    await queryRunner.query(
      `CREATE TABLE "event" ("id" SERIAL NOT NULL, "sourceId" text NOT NULL, "type" "public"."event_type_enum" NOT NULL, "time" TIMESTAMP WITH TIME ZONE NOT NULL, "amount" double precision NOT NULL, "toId" integer, "fromId" integer, CONSTRAINT "PK_82ff22c1314984ac7b8cade26a6" PRIMARY KEY ("id", "time"))`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_8eb34e6d33033e17e91776c1c2" ON "event" ("sourceId", "time") `,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_82ff22c1314984ac7b8cade26a" ON "event" ("id", "time") `,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_46f304d2b1e02a2ce46d43403e" ON "event" ("time") `,
    );
    await queryRunner.query(
      `CREATE TABLE "event_pointer" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "collector" text NOT NULL, "startDate" TIMESTAMP WITH TIME ZONE NOT NULL, "endDate" TIMESTAMP WITH TIME ZONE NOT NULL, "version" integer NOT NULL, "artifactId" integer, CONSTRAINT "PK_602eaa0f5966ca040d2835d8cd9" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_3d92caafdc685cc487ce201b49" ON "event_pointer" ("artifactId", "collector", "startDate", "endDate") `,
    );
    await queryRunner.query(
      `CREATE TABLE "job" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "execGroup" text NOT NULL, "scheduledTime" TIMESTAMP WITH TIME ZONE NOT NULL, "collector" text NOT NULL, "status" "public"."job_status_enum" NOT NULL, CONSTRAINT "PK_98ab1c14ff8d1cf80d18703b92f" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE TABLE "job_execution" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "status" "public"."job_execution_status_enum" NOT NULL, "jobId" integer, CONSTRAINT "PK_81e54343e6d62f09a166d105792" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE TABLE "log" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "level" text NOT NULL, "body" jsonb NOT NULL, "executionId" integer, CONSTRAINT "PK_350604cbdf991d5930d9e618fbd" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE TABLE "collection_projects_project" ("collectionId" integer NOT NULL, "projectId" integer NOT NULL, CONSTRAINT "PK_4d933f2f3a834897250ca67fb20" PRIMARY KEY ("collectionId", "projectId"))`,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_44350998a09c6306a61f6854d2" ON "collection_projects_project" ("collectionId") `,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_d38703155092b0b8b0779b43dd" ON "collection_projects_project" ("projectId") `,
    );
    await queryRunner.query(
      `CREATE TABLE "project_artifacts_artifact" ("projectId" integer NOT NULL, "artifactId" integer NOT NULL, CONSTRAINT "PK_c0174962d1f020db7458cf5810a" PRIMARY KEY ("projectId", "artifactId"))`,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_baaddcf9097758446307cd9825" ON "project_artifacts_artifact" ("projectId") `,
    );
    await queryRunner.query(
      `CREATE INDEX "IDX_fad8b476b66052b4e2a5653cf5" ON "project_artifacts_artifact" ("artifactId") `,
    );
    await queryRunner.query(
      `ALTER TABLE "event" ADD CONSTRAINT "FK_404b3d263eafc41aae2044e9b85" FOREIGN KEY ("toId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "event" ADD CONSTRAINT "FK_b36ab188856dd8cf3d6c7ec4f48" FOREIGN KEY ("fromId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "event_pointer" ADD CONSTRAINT "FK_afa2cb33377e4c90a7c6d6a3a66" FOREIGN KEY ("artifactId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "job_execution" ADD CONSTRAINT "FK_6f342ebe2b66a1c613516efa7db" FOREIGN KEY ("jobId") REFERENCES "job"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "log" ADD CONSTRAINT "FK_d4bef9bfb811b441cb8ecb115eb" FOREIGN KEY ("executionId") REFERENCES "job_execution"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "collection_projects_project" ADD CONSTRAINT "FK_44350998a09c6306a61f6854d23" FOREIGN KEY ("collectionId") REFERENCES "collection"("id") ON DELETE CASCADE ON UPDATE CASCADE`,
    );
    await queryRunner.query(
      `ALTER TABLE "collection_projects_project" ADD CONSTRAINT "FK_d38703155092b0b8b0779b43dd3" FOREIGN KEY ("projectId") REFERENCES "project"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(
      `ALTER TABLE "project_artifacts_artifact" ADD CONSTRAINT "FK_baaddcf9097758446307cd9825d" FOREIGN KEY ("projectId") REFERENCES "project"("id") ON DELETE CASCADE ON UPDATE CASCADE`,
    );
    await queryRunner.query(
      `ALTER TABLE "project_artifacts_artifact" ADD CONSTRAINT "FK_fad8b476b66052b4e2a5653cf5f" FOREIGN KEY ("artifactId") REFERENCES "artifact"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );
    await queryRunner.query(`SELECT create_hypertable('event', 'time')`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "project_artifacts_artifact" DROP CONSTRAINT "FK_fad8b476b66052b4e2a5653cf5f"`,
    );
    await queryRunner.query(
      `ALTER TABLE "project_artifacts_artifact" DROP CONSTRAINT "FK_baaddcf9097758446307cd9825d"`,
    );
    await queryRunner.query(
      `ALTER TABLE "collection_projects_project" DROP CONSTRAINT "FK_d38703155092b0b8b0779b43dd3"`,
    );
    await queryRunner.query(
      `ALTER TABLE "collection_projects_project" DROP CONSTRAINT "FK_44350998a09c6306a61f6854d23"`,
    );
    await queryRunner.query(
      `ALTER TABLE "log" DROP CONSTRAINT "FK_d4bef9bfb811b441cb8ecb115eb"`,
    );
    await queryRunner.query(
      `ALTER TABLE "job_execution" DROP CONSTRAINT "FK_6f342ebe2b66a1c613516efa7db"`,
    );
    await queryRunner.query(
      `ALTER TABLE "event_pointer" DROP CONSTRAINT "FK_afa2cb33377e4c90a7c6d6a3a66"`,
    );
    await queryRunner.query(
      `ALTER TABLE "event" DROP CONSTRAINT "FK_b36ab188856dd8cf3d6c7ec4f48"`,
    );
    await queryRunner.query(
      `ALTER TABLE "event" DROP CONSTRAINT "FK_404b3d263eafc41aae2044e9b85"`,
    );
    await queryRunner.query(
      `DROP INDEX "public"."IDX_fad8b476b66052b4e2a5653cf5"`,
    );
    await queryRunner.query(
      `DROP INDEX "public"."IDX_baaddcf9097758446307cd9825"`,
    );
    await queryRunner.query(`DROP TABLE "project_artifacts_artifact"`);
    await queryRunner.query(
      `DROP INDEX "public"."IDX_d38703155092b0b8b0779b43dd"`,
    );
    await queryRunner.query(
      `DROP INDEX "public"."IDX_44350998a09c6306a61f6854d2"`,
    );
    await queryRunner.query(`DROP TABLE "collection_projects_project"`);
    await queryRunner.query(`DROP TABLE "log"`);
    await queryRunner.query(`DROP TABLE "job_execution"`);
    await queryRunner.query(`DROP TABLE "job"`);
    await queryRunner.query(
      `DROP INDEX "public"."IDX_3d92caafdc685cc487ce201b49"`,
    );
    await queryRunner.query(`DROP TABLE "event_pointer"`);
    await queryRunner.query(
      `DROP INDEX "public"."IDX_46f304d2b1e02a2ce46d43403e"`,
    );
    await queryRunner.query(
      `DROP INDEX "public"."IDX_82ff22c1314984ac7b8cade26a"`,
    );
    await queryRunner.query(
      `DROP INDEX "public"."IDX_8eb34e6d33033e17e91776c1c2"`,
    );
    await queryRunner.query(`DROP TABLE "event"`);
    await queryRunner.query(
      `DROP INDEX "public"."IDX_1b59a64c744d72143d2b96b2c7"`,
    );
    await queryRunner.query(`DROP TABLE "artifact"`);
    await queryRunner.query(`DROP TABLE "project"`);
    await queryRunner.query(`DROP TABLE "collection"`);
  }
}
