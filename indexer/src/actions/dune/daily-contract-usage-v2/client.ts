/**
 * A client for our daily contract usage query on Dune
 *
 * The client will resolve everything in the request to raw addresses as we
 * currently use a method for querying dune that involves passing in
 * known-user-addresses + ids and known-contract-addresses + ids. This reduces
 * the burden of the api calls on our quota by about 20% in testing.
 */
import { DateTime } from "luxon";
import fs from "fs";

import { IDuneClient } from "../../../utils/dune/type.js";
import { parse } from "csv";
import { assert } from "../../../utils/common.js";
import { QueryParameter } from "@cowprotocol/ts-dune-client";
import { Range } from "../../../utils/ranges.js";
import path from "path";
import _ from "lodash";
import { readFile, writeFile } from "fs/promises";

class SafeAggregate {
  rows: DailyContractUsageRow[];

  constructor(first: DailyContractUsageRow) {
    this.rows = [first];
  }

  aggregate(): DailyContractUsageRow {
    const rows = this.rows;
    return this.rows.slice(1).reduce<DailyContractUsageRow>((agg, curr) => {
      const row = curr;
      const gasCostBI = BigInt(agg.gasCostGwei) + BigInt(row.gasCostGwei);
      return {
        date: agg.date,
        contractAddress: agg.contractAddress,
        userAddress: agg.userAddress,
        safeAddress: agg.safeAddress,
        txCount: agg.txCount + row.txCount,
        gasCostGwei: gasCostBI.toString(10),
      };
    }, this.rows[0]);
  }

  add(row: DailyContractUsageRow) {
    this.rows.push(row);
  }

  get count() {
    return this.rows.length;
  }
}

export type DailyContractUsageRow = {
  date: string;
  contractAddress: string;
  userAddress: string | null;
  safeAddress: string | null;
  gasCostGwei: string;
  txCount: number;
};

export type DailyContractUsageRawRow = {
  date: string;
  contractId: number;
  userAddress: string | null;
  safeAddress: string | null;
  gasCostGwei: string;
  txCount: number;
};

export interface IDailyContractUsageClientV2 {
  getDailyContractUsage(range: Range, contractSha1: string): Promise<DailyContractUsageRow[]>;
  getDailyContractUsageFromCsv(date: DateTime, contractSha1: string): Promise<DailyContractUsageRow[]>;

}

export interface DailyContractUsageClientOptions {
  queryId: number;

  // Tables directory
  tablesDirectoryPath: string;

  // Load from CSV Path
  csvDirPath: string;
}

export const DefaultDailyContractUsageClientOptions: DailyContractUsageClientOptions =
{
  // This default is based on this: https://dune.com/queries/3083184
  queryId: 3083184,

  tablesDirectoryPath: "",

  csvDirPath: "",
};

export type Addresses = string[];

export type DuneRawUsageItem = [
  // eoa
  string | null,
  // safe
  string | null,
  // totalGasCostForUser - gasFees * gasPrice for each user
  string,
  // txCount - number of transactions
  number,
];

export interface DuneRawRow {
  date: string;
  contract_id: number;
  usage: DuneRawUsageItem[];
}

export function parseDuneContractUsageCSVRow(row: string[]): DuneRawRow {
  // Parse the array of values from inside of the dune row
  const usageArray = parseDuneCSVArray(row[2]);
  const usage: DuneRawUsageItem[] = usageArray.map((u) => {
    // Check the types
    assert(!Array.isArray(u[0]), "eoa address should be a string");
    assert(!Array.isArray(u[1]), "safe address should be a string");
    assert(!Array.isArray(u[2]), "gas costs should be a string");
    assert(!Array.isArray(u[3]), "call count should be a string");

    return [
      u[0] === "<nil>" ? null : (u[0] as string),
      u[1] === "<nil>" ? null : (u[1] as string),
      u[2] as string,
      parseInt(u[3] as string),
    ];
  });
  return {
    date: row[0],
    contract_id: parseInt(row[1]),
    usage: usage,
  };
}

export function transformDuneRawRowToUsageRows(
  row: DuneRawRow,
  contractsMap: Record<number, string>,
): DailyContractUsageRow[] {
  const rows = transformDuneRawRowToUsageRawRows(row);
  return rows.map((r) => {
    return {
      date: r.date,
      contractAddress: contractsMap[r.contractId],
      userAddress: r.userAddress,
      safeAddress: r.safeAddress,
      gasCostGwei: r.gasCostGwei,
      txCount: r.txCount,
    };
  });
}

export function transformDuneRawRowToUsageRawRows(
  row: DuneRawRow,
): DailyContractUsageRawRow[] {
  const date = DateTime.fromSQL(row.date).toUTC().toISO();
  if (date === null) {
    throw new Error("invalid date");
  }

  // Expand raw rows into more rows
  return row.usage.map((usage) => {
    return {
      date: date,
      contractId: row.contract_id,
      userAddress: usage[0],
      safeAddress: usage[1],
      gasCostGwei: usage[2],
      txCount: usage[3],
    };
  });
}

type ParsedArrayValue = string | ParsedArrayValue[];

export function parseDuneCSVArray(arrayString: string): ParsedArrayValue[] {
  // Simple recursive scan to parse
  const recursiveParser = (
    index: number,
    depth: number,
  ): [ParsedArrayValue[], number] => {
    if (depth > 2) {
      console.log("GOING DEEEEEEEEEEEEEEP");
      console.log(depth);
    }
    index += 1;

    const result: ParsedArrayValue[] = [];
    let buffer = "";

    while (index < arrayString.length) {
      if (arrayString[index] == "]") {
        if (buffer !== "") {
          result.push(buffer);
        }
        return [result, index + 1];
      }
      if (arrayString[index] == "[") {
        const [res, nextIndex] = recursiveParser(index, depth + 1);
        index = nextIndex;
        result.push(res);
        continue;
      }
      if (arrayString[index] != " ") {
        buffer += arrayString[index];
      }
      // We've reached the end of this string.
      if (arrayString[index] == " " && buffer !== "") {
        result.push(buffer);
        buffer = "";
      }
      index += 1;
    }
    throw new Error("Invalid data. An array is unterminated");
  };
  return recursiveParser(0, 0)[0];
}

type ContractTableRow = {
  id: string,
  address: string,
}

export function loadContractsTable(path: string): Promise<ContractTableRow[]> {
  const stream = fs.createReadStream(path);
  const result: ContractTableRow[] = [];

  return new Promise((resolve, reject) => {
    return stream
      .pipe(parse({ delimiter: ",", fromLine: 2 }))
      .on('data', (row) => {
        result.push({
          id: row[0],
          address: row[1],
        })
      })
      .on("error", (err) => {
        reject(err);
      })
      .on('finish', () => {
        resolve(result);
      })
  });
}

export interface IDailyContractUsageResponse {
  uniqueUserAddresses(): string[];
  contractAddresses(): string[];
  toJSON(): string;
  mapRowsByContractAddress<R>(
    cb: (contractAddress: string, rows: DailyContractUsageRow[]) => R,
  ): Array<R>;
}

export class DailyContractUsageClient implements IDailyContractUsageClientV2 {
  private client: IDuneClient;
  private options: DailyContractUsageClientOptions;

  constructor(
    client: IDuneClient,
    options?: Partial<DailyContractUsageClientOptions>,
  ) {
    this.client = client;
    this.options = _.merge(DefaultDailyContractUsageClientOptions, options);
  }

  /**
   * Refreshes our dune [query](https://dune.com/queries/3083184) to resolve the
   * daily contract usage. This uses a pre-uploaded version of the contract
   * addresses that we store in this database. When the monitored contracts
   * changes, we need to upload a new version to dune. 
   *
   * @param range The date range for the query execution
   * @param contractsSha1 sha1 of the data used for the uploaded csv
   */
  async getDailyContractUsage(
    range: Range,
    contractSha1: string = "da1aae77b853fc7c74038ee08eec441b10b89570",
  ): Promise<DailyContractUsageRow[]> {
    // Load the contracts table
    const contractsMap = await this.loadContractsTable(contractSha1)

    const parameters = [
      QueryParameter.text(
        "start_time",
        range.startDate.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
      ),
      QueryParameter.text(
        "end_time",
        range.endDate.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
      ),
      QueryParameter.text(
        "contracts_table",
        contractSha1,
      )
    ];

    //const response = await this.client.refresh(this.options.queryId, parameters);
    const response = JSON.parse(await readFile('tester-123456.json', { encoding: 'utf-8' })) as Awaited<ReturnType<IDuneClient["refresh"]>>;
    //await writeFile('tester-123456.json', JSON.stringify(response));
    const rawRows = (response.result?.rows as unknown[]) as DuneRawRow[];

    console.log('lens');
    console.log(response.result?.rows.length);

    const currentDate = DateTime.fromSQL(rawRows[0].date);

    // Split raw rows by date
    const rowsByDay = rawRows.reduce<Record<string, DuneRawRow[]>>((acc, curr) => {
      // Update the date value to be ISO 
      const rowsForDate = acc[curr.date] || [];
      rowsForDate.push(curr);
      acc[curr.date] = rowsForDate
      return acc;
    }, {});

    console.log(Object.keys(rowsByDay));

    const sortedDates = Object.keys(rowsByDay).sort();
    console.log(sortedDates);
    const rows: DailyContractUsageRow[] = [];
    for (const date of sortedDates) {
      console.log('i am here')
      const rawRows = rowsByDay[date];
      rows.push(...this.expandRowsForDate(contractsMap, rawRows));
    }

    console.log(`expanded rows now: ${rows.length}`);

    // Aggregate safes. Not sure why but sometimes the data isn't being
    // aggregated on the Dune side.
    return rows;
  }

  expandRowsForDate(contractsMap: Record<number, string>, rawRows: DuneRawRow[]): DailyContractUsageRow[] {
    console.log('i am here2')
    const usageRows: DailyContractUsageRow[] = [];

    const safes: Record<string, SafeAggregate> = {};
    for (const rawRow of rawRows) {
      console.log('i am here3')
      let expandedRows: DailyContractUsageRow[] = [];
      try {
        expandedRows = transformDuneRawRowToUsageRows(rawRow, contractsMap);
      } catch (err) {
        console.log('what the fuck?');
        console.log('i failed i guess')
        console.error(err);
      }
      console.log('i am here4')
      for (const usageRow of expandedRows) {
        console.log(usageRow);
        if (usageRow.safeAddress) {
          const address = usageRow.safeAddress.toLowerCase();
          if (safes[address]) {
            safes[address].add(usageRow);
          } else {
            safes[address] = new SafeAggregate(usageRow);
          }
        } else {
          usageRows.push(usageRow);
        }
      }
    }
    for (const address in safes) {
      const safe = safes[address];
      usageRows.push(safe.aggregate());
    }
    return usageRows;
  }

  async getDailyContractUsageFromCsv(date: DateTime, contractSha1: string = "da1aae77b853fc7c74038ee08eec441b10b89570"): Promise<DailyContractUsageRow[]> {
    return this.loadCsvPath(
      `/data/tmp/oso/dune-backfill/${date.toISODate()}.csv`,
    );
  }

  async loadContractsTable(sha: string): Promise<Record<number, string>> {
    const contracts = await loadContractsTable(path.join(this.options.tablesDirectoryPath, `contracts-${sha}.csv`));

    return contracts.reduce<Record<number, string>>((acc, curr) => {
      const id = parseInt(curr.id);
      acc[id] = curr.address;
      return acc;
    }, {})
  }

  async loadCsvPath(path: string) {
    console.log(`path=${path}`);
    return new Promise<DailyContractUsageRow[]>((resolve, reject) => {
      setImmediate(() => {
        const rows: DailyContractUsageRow[] = [];
        const stream = fs.createReadStream(path);
        return stream
          .pipe(parse({ delimiter: ",", fromLine: 1 }))
          .on("data", (chunk) => {
            const row: DailyContractUsageRow = {
              date: chunk[0],
              contractAddress: chunk[1],
              userAddress: chunk[2] === "" ? null : chunk[2],
              safeAddress: chunk[3] === "" ? null : chunk[3],
              gasCostGwei: chunk[4],
              txCount: parseInt(chunk[5], 10),
            };
            rows.push(row);
          })
          .on("error", (err) => {
            return reject(err);
          })
          .on("finish", () => {
            resolve(rows);
          });
      });
    });
  }
}
