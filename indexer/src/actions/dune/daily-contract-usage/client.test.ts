import { DateTime, Duration } from "luxon";

import {
  resolveDailyContractUsage,
  IdToAddressMap,
  DailyContractUsageRawRow,
} from "./client.js";
import _ from "lodash";

describe("resolveDailyContractUsageResults", () => {
  const fakeUserIdToAddressMap: IdToAddressMap = {
    0: "0x0000000000000000000000000000000000000000",
    1: "0x0000000000000000000000000000000000000001",
    2: "0x0000000000000000000000000000000000000002",
  };

  const fakeContractIdToAddressMap: IdToAddressMap = {
    0: "0xc000000000000000000000000000000000000000",
    1: "0xc000000000000000000000000000000000000001",
    2: "0xc000000000000000000000000000000000000002",
  };

  const fakeEndDate = DateTime.now();
  const fakeStartDate = fakeEndDate.minus(Duration.fromObject({ days: 7 }));

  test("resolve rows correctly", () => {
    const rows: DailyContractUsageRawRow[] = [
      {
        date: "2023-01-01 00:00:00 UTC",
        contract_id: 0,
        user_addresses: [],
        user_ids: [0, 2],
        contract_total_tx_count: 1,
        contract_total_l2_gas_cost_gwei: "0",
        safe_address_count: 0,
      },
      {
        date: "2023-01-01 00:00:00 UTC",
        contract_id: 1,
        user_addresses: ["0x0000000000000000000000000000000000000004"],
        user_ids: [1, 2],
        contract_total_tx_count: 1,
        contract_total_l2_gas_cost_gwei: "0",
        safe_address_count: 0,
      },
    ];
    const resolved = resolveDailyContractUsage(
      fakeUserIdToAddressMap,
      fakeContractIdToAddressMap,
      rows,
    );

    expect(resolved[0].contractAddress).toBe(
      "0xc000000000000000000000000000000000000000",
    );
    expect(resolved[0].userAddresses.length).toBe(2);
    expect(resolved[0].userAddresses).toEqual(
      expect.arrayContaining([
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000002",
      ]),
    );

    expect(resolved[1].contractAddress).toBe(
      "0xc000000000000000000000000000000000000001",
    );
    expect(resolved[1].userAddresses.length).toBe(3);
    expect(resolved[1].userAddresses).toEqual(
      expect.arrayContaining([
        "0x0000000000000000000000000000000000000004",
        "0x0000000000000000000000000000000000000001",
        "0x0000000000000000000000000000000000000002",
      ]),
    );
  });

  test("errors when resolving a row with a non-existent user-id", () => {
    const rows: DailyContractUsageRawRow[] = [
      {
        date: "2023-01-01 00:00:00 UTC",
        contract_id: 0,
        user_addresses: [],
        user_ids: [10],
        contract_total_tx_count: 1,
        contract_total_l2_gas_cost_gwei: "0",
        safe_address_count: 0,
      },
    ];
    expect(() => {
      resolveDailyContractUsage(
        fakeUserIdToAddressMap,
        fakeContractIdToAddressMap,
        rows,
      );
    }).toThrowError();
  });
});
