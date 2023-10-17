import { MigrationInterface, QueryRunner } from "typeorm";

// The original EventType enum used before this migration
enum OriginalEventType {
  FUNDING = "FUNDING",
  PULL_REQUEST_CREATED = "PULL_REQUEST_CREATED",
  PULL_REQUEST_MERGED = "PULL_REQUEST_MERGED",
  COMMIT_CODE = "COMMIT_CODE",
  ISSUE_FILED = "ISSUE_FILED",
  ISSUE_CLOSED = "ISSUE_CLOSED",
  DOWNSTREAM_DEPENDENCY_COUNT = "DOWNSTREAM_DEPENDENCY_COUNT",
  UPSTREAM_DEPENDENCY_COUNT = "UPSTREAM_DEPENDENCY_COUNT",
  DOWNLOADS = "DOWNLOADS",
  CONTRACT_INVOKED = "CONTRACT_INVOKED",
  USERS_INTERACTED = "USERS_INTERACTED",
  CONTRACT_INVOKED_AGGREGATE_STATS = "CONTRACT_INVOKED_AGGREGATE_STATS",
  PULL_REQUEST_CLOSED = "PULL_REQUEST_CLOSED",
  STAR_AGGREGATE_STATS = "STAR_AGGREGATE_STATS",
  PULL_REQUEST_REOPENED = "PULL_REQUEST_REOPENED",
  PULL_REQUEST_REMOVED_FROM_PROJECT = "PULL_REQUEST_REMOVED_FROM_PROJECT",
  PULL_REQUEST_APPROVED = "PULL_REQUEST_APPROVED",
  ISSUE_CREATED = "ISSUE_CREATED",
  ISSUE_REOPENED = "ISSUE_REOPENED",
  ISSUE_REMOVED_FROM_PROJECT = "ISSUE_REMOVED_FROM_PROJECT",
  STARRED = "STARRED",
  FORK_AGGREGATE_STATS = "FORK_AGGREGATE_STATS",
  FORKED = "FORKED",
  WATCHER_AGGREGATE_STATS = "WATCHER_AGGREGATE_STATS",
}

export class AllowMoveToEventTypeTable1697488360700
  implements MigrationInterface
{
  name = "AllowMoveToEventTypeTable1697488360700";

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE "event_type" ("id" SERIAL NOT NULL, "createdAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "updatedAt" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(), "deletedAt" TIMESTAMP WITH TIME ZONE, "name" character varying(50) NOT NULL, "version" smallint NOT NULL, CONSTRAINT "PK_d968f34984d7d85d96f782872fe" PRIMARY KEY ("id"))`,
    );
    await queryRunner.query(
      `CREATE UNIQUE INDEX "IDX_512d8bcc602d7561a096a46395" ON "event_type" ("name", "version") `,
    );
    await queryRunner.query(`ALTER TABLE "event" ADD "typeId" integer`);
    await queryRunner.query(
      `ALTER TABLE "event" ADD CONSTRAINT "FK_255cc0faa667931c91431716165" FOREIGN KEY ("typeId") REFERENCES "event_type"("id") ON DELETE NO ACTION ON UPDATE NO ACTION`,
    );

    const enumValues = Object.keys(OriginalEventType);
    const keys = Object.values(enumValues);

    // Initialize the event type table. Not worrying about sql injection
    // here. We're the ones providing input.
    await queryRunner.query(
      `
      insert into event_type(name, version)
      select unnest($1::text[]), 1
    `,
      [keys],
    );

    // Fill the fields with the correct values from the new event type table
    await queryRunner.query(`
      update event e
      set "typeId" = et.id
      from event_type et where et.name = e.type::TEXT
    `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "event" DROP CONSTRAINT "FK_255cc0faa667931c91431716165"`,
    );
    await queryRunner.query(`ALTER TABLE "event" DROP COLUMN "typeId"`);
    await queryRunner.query(
      `DROP INDEX "public"."IDX_512d8bcc602d7561a096a46395"`,
    );
    await queryRunner.query(`DROP TABLE "event_type"`);
  }
}
