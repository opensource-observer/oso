import { MigrationInterface, QueryRunner } from "typeorm";

export class SplitContractInvokedEvents1697508826281
  implements MigrationInterface
{
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Create the new event types
    const events = [
      "CONTRACT_INVOCATION_DAILY_COUNT",
      "CONTRACT_INVOCATION_DAILY_FEES",
    ];

    await queryRunner.query(
      `
      insert into event_type(name, version)
      select unnest($1::text[]), 1
    `,
      [events],
    );

    console.log(
      await queryRunner.query(`
      select * from event_type et where et.name = 'CONTRACT_INVOCATION_DAILY_FEES' and et.version = 1
    `),
    );

    console.log(
      await queryRunner.query(`
      select * from event_type et where et.name = 'CONTRACT_INVOCATION_DAILY_COUNT' and et.version = 1
    `),
    );

    // Create the `CONTRACT_INVOCATION_DAILY_COUNT` from the `CONTRACT_INVOKED` event
    await queryRunner.query(`
      with cidc_et as (
        select * from event_type et where et.name = 'CONTRACT_INVOCATION_DAILY_COUNT' and et.version = 1
      )
      insert into event("sourceId", "typeId", "time", "toId", "fromId", "amount")
      select e."sourceId", (select "id" from cidc_et), e."time", e."toId", e."fromId", e."amount"
      from event e
      join event_type insert_et 
        on insert_et."id" = e."typeId"
      where insert_et."name" = 'CONTRACT_INVOKED'
    `);
    await queryRunner.query(`
      with cidf_et as (
        select * from event_type et where et.name = 'CONTRACT_INVOCATION_DAILY_FEES' and et.version = 1
      )
      insert into event("sourceId", "typeId", "time", "toId", "fromId", "amount")
      select e."sourceId", (select "id" from cidf_et), e."time", e."toId", e."fromId", CAST(e."size" as float)
      from event e
      join event_type insert_et 
        on insert_et."id" = e."typeId"
      where insert_et."name" = 'CONTRACT_INVOKED'
    `);
    await queryRunner.query(`
      delete from event e 
      using event_type et
      where e."typeId" = et."id" and et."name" = 'CONTRACT_INVOKED'
    `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      with ci_et as (
        select * from event_type et where et.name = 'CONTRACT_INVOKED' and et.version = 1
      )
      insert into event("sourceId", "typeId", "time", "toId", "fromId", "amount", "size")
      select 
        count_e."sourceId", 
        (select c.id from ci_et c), 
        count_e."time", 
        count_e."toId", 
        count_e."fromId", 
        count_e."amount", 
        CAST(fee_e.amount as bigint)
      from 
        (
          select 
            * 
          from 
            event inner_count_e 
          inner join event_type ice_et
            on ice_et.id = inner_count_e.typeId
          where 
            ice_et."name" = 'CONTRACT_INVOCATION_DAILY_COUNT'
        ) as count_e 
      inner join 
        (
          select 
            * 
          from 
            event inner_fee_e 
          inner join event_type ife_et
            on icf_et.id = inner_count_e.typeId
          where 
            ife_et."name" = 'CONTRACT_INVOCATION_DAILY_FEE'
        ) as fee_e
    `);
    await queryRunner.query(`
      delete from event e 
      using event_type et
      where e."typeId" = et."id" and et."name" IN ('CONTRACT_INVOCATION_DAILY_FEES', 'CONTRACT_INVOCATION_DAILY_COUNT')
    `);

    await queryRunner.query(`
      delete from event_type et
      where e."name" IN ('CONTRACT_INVOCATION_DAILY_FEES', 'CONTRACT_INVOCATION_DAILY_COUNT')
    `);
  }
}
