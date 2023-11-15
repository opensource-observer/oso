import { MigrationInterface, QueryRunner } from "typeorm";

const GAS_USED_EVENT_TYPES = [
  "CONTRACT_INVOCATION_DAILY_L2_GAS_USED",
  "CONTRACT_INVOCATION_DAILY_L1_GAS_USED",
];

export class AddGasUsedEvents1700078985727 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `
      insert into event_type(name, version)
      select unnest($1::text[]), 1
    `,
      [GAS_USED_EVENT_TYPES],
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `
      delete from event_type et
      where et."name" = ANY($1) AND et."version" = 1
    `,
      [GAS_USED_EVENT_TYPES],
    );
  }
}
