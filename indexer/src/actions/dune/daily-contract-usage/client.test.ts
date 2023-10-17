import {
  parseDuneContractUsageCSVRow,
  DuneRawRow,
  parseDuneCSVArray,
  SafeAggregate,
  DailyContractUsageRow,
} from "./client.js";
import { parse } from "csv/sync";

// CSV Snippet that's easy to read
const contractCsvSnippet0 = `
date,contract_id,usage
2022-08-28 00:00:00.000 UTC,123,[[0x1111111111111111111111111111111111111111 0x1111111111111111111111111111111111111111 1000000 1] [0x2222222222222222222222222222222222222222 <nil> 2000000000000 2] [<nil> 0x3333333333333333333333333333333333333333 3000000000000000000000000 3]]
`.trim();

const expectedContractCsvSnippet0: DuneRawRow = {
  date: "2022-08-28 00:00:00.000 UTC",
  contract_id: 123,
  usage: [
    [
      "0x1111111111111111111111111111111111111111",
      "0x1111111111111111111111111111111111111111",
      "1000000",
      1,
    ],
    ["0x2222222222222222222222222222222222222222", null, "2000000000000", 2],
    [
      null,
      "0x3333333333333333333333333333333333333333",
      "3000000000000000000000000",
      3,
    ],
  ],
};

describe("resolveDailyContractUsageResults", () => {
  test("should parse the csv rows from dune", () => {
    const parsed = parse(contractCsvSnippet0) as string[][];
    const result = parseDuneContractUsageCSVRow(parsed[1]);
    expect(result).toEqual(expectedContractCsvSnippet0);
  });

  test("should parse generic csv array from dune", () => {
    const csvArray0 = "[1234 <nil> test0]";
    const expectedArray0 = ["1234", "<nil>", "test0"];
    const csvArray1 = "[4567 test1 <nil>]";
    const expectedArray1 = ["4567", "test1", "<nil>"];
    // Nested Array
    const csvArrayNested0 = `[${csvArray0} ${csvArray1}]`;
    expect(parseDuneCSVArray(csvArray0)).toEqual(expectedArray0);
    expect(parseDuneCSVArray(csvArray1)).toEqual(expectedArray1);
    expect(parseDuneCSVArray(csvArrayNested0)).toEqual([
      expectedArray0,
      expectedArray1,
    ]);
  });

  test("should throw error when parsing generic csv array from dune that is poorly formatted", () => {
    const csvArray0 = "[1234 <nil> test0";
    // Nested Array
    expect(() => {
      parseDuneCSVArray(csvArray0);
    }).toThrow();
  });
});

describe("SafeAggregate", () => {
  const safesToAggregate: DailyContractUsageRow[] = [
    {
      date: "2023-10-11T00:00:00Z",
      contractAddress: "0x1111111111111111111111111111111111111111",
      userAddress: null,
      safeAddress: "0x1111111111111111111111111111111111111111",
      gasCostGwei: "10000",
      txCount: 11,
    },
    {
      date: "2023-10-11T00:00:00Z",
      contractAddress: "0x1111111111111111111111111111111111111111",
      userAddress: null,
      safeAddress: "0x1111111111111111111111111111111111111111",
      gasCostGwei: "20000",
      txCount: 22,
    },
    {
      date: "2023-10-11T00:00:00Z",
      contractAddress: "0x1111111111111111111111111111111111111111",
      userAddress: null,
      safeAddress: "0x1111111111111111111111111111111111111111",
      gasCostGwei: "30000",
      txCount: 33,
    },
  ];

  test("should aggregrate safe values in the csv", () => {
    const aggregator = new SafeAggregate(safesToAggregate[0]);

    for (const safe of safesToAggregate.slice(1)) {
      aggregator.add(safe);
    }
    const agg = aggregator.aggregate();
    expect(agg.contractAddress).toEqual(
      "0x1111111111111111111111111111111111111111",
    );
    expect(agg.safeAddress).toEqual(
      "0x1111111111111111111111111111111111111111",
    );
    expect(agg.userAddress).toBeNull();
    expect(agg.gasCostGwei).toEqual("60000");
    expect(agg.txCount).toEqual(66);
  });
});
