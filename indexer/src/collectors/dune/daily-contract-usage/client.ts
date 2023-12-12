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
import { logger } from "../../../utils/logger.js";
import { UniqueArray } from "../../../utils/array.js";
import { sha1FromArray } from "../../../utils/source-ids.js";
import { DuneCSVUploader } from "../utils/csv-uploader.js";

export function stringToBigInt(x: string) {
  try {
    return BigInt(x);
  } catch (_err) {
    return BigInt(parseFloat(x));
  }
}

export function stringToInt(x: string) {
  // If it contains a scientific notation. parse as a float.
  if (x.indexOf("e") !== -1) {
    return parseFloat(x);
  }

  return parseInt(x);
}

export class SafeAggregate {
  rows: DailyContractUsageRow[];
  id: string;

  constructor(first: DailyContractUsageRow) {
    this.rows = [first];
  }

  aggregate(): DailyContractUsageRow {
    return this.rows.slice(1).reduce<DailyContractUsageRow>((agg, curr) => {
      const row = curr;
      const l2GasUsed =
        stringToBigInt(agg.l2GasUsed) + stringToBigInt(row.l2GasUsed);
      const l1GasUsed =
        stringToBigInt(agg.l1GasUsed) + stringToBigInt(row.l1GasUsed);
      return {
        date: agg.date,
        contractAddress: agg.contractAddress,
        userAddress: agg.userAddress,
        safeAddress: agg.safeAddress,
        txCount: agg.txCount + row.txCount,
        l2GasUsed: l2GasUsed.toString(10),
        l1GasUsed: l1GasUsed.toString(10),
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
  l2GasUsed: string;
  l1GasUsed: string;
  txCount: number;
};

export type DailyContractUsageRawRow = {
  date: string;
  contractId: number;
  userAddress: string | null;
  safeAddress: string | null;
  l2GasUsed: string;
  l1GasUsed: string;
  txCount: number;
};

export type Contract = {
  id: number;
  address: string;
};

export type ContractTableReference = {
  contracts?: Contract[];
  tableId?: string;
};

export interface IDailyContractUsageClientV2 {
  getDailyContractUsage(
    range: Range,
    contractTableReference: ContractTableReference,
  ): Promise<DailyContractUsageRow[]>;
  getDailyContractUsageFromCsv(
    date: DateTime,
  ): Promise<DailyContractUsageRow[]>;
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
    // This default is based on this: https://dune.com/queries/3198847
    queryId: 3198847,

    tablesDirectoryPath: "",

    csvDirPath: "",
  };

export type Addresses = string[];

export type DuneRawUsageItem = [
  // eoa
  string | null,
  // safe
  string | null,
  // totalL2GasUsedForUser
  string,
  // totalL1GasUsedForUser
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
    assert(!Array.isArray(u[2]), "l2 gas used should be a string");
    assert(!Array.isArray(u[3]), "l1 gas used should be a string");
    assert(!Array.isArray(u[4]), "call count should be a string");

    return [
      u[0] === "<nil>" ? null : (u[0] as string),
      u[1] === "<nil>" ? null : (u[1] as string),
      u[2] as string,
      u[3] as string,
      stringToInt(u[4] as string),
    ];
  });
  return {
    date: row[0],
    contract_id: stringToInt(row[1]),
    usage: usage,
  };
}

export function transformDuneRawRowToUsageRows(
  row: DuneRawRow,
  contractsMap: Record<number, string>,
): DailyContractUsageRow[] {
  const rows = transformDuneRawRowToUsageRawRows(row);

  return rows.map((r) => {
    if (!contractsMap[r.contractId]) {
      throw new Error(`missing contract address for ${r.contractId} in map`);
    }
    return {
      date: r.date,
      contractAddress: contractsMap[r.contractId],
      userAddress: r.userAddress,
      safeAddress: r.safeAddress,
      l2GasUsed: r.l2GasUsed,
      l1GasUsed: r.l1GasUsed,
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
      l2GasUsed: usage[2],
      l1GasUsed: usage[3],
      txCount: usage[4],
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
  id: string;
  address: string;
};

export function loadContractsTable(path: string): Promise<ContractTableRow[]> {
  const stream = fs.createReadStream(path);
  const result: ContractTableRow[] = [];

  return new Promise((resolve, reject) => {
    return stream
      .pipe(parse({ delimiter: ",", fromLine: 2 }))
      .on("data", (row) => {
        result.push({
          id: row[0],
          address: row[1],
        });
      })
      .on("error", (err) => {
        reject(err);
      })
      .on("finish", () => {
        resolve(result);
      });
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
  private uploader: DuneCSVUploader;
  private options: DailyContractUsageClientOptions;

  constructor(
    client: IDuneClient,
    uploader: DuneCSVUploader,
    options?: Partial<DailyContractUsageClientOptions>,
  ) {
    this.client = client;
    this.uploader = uploader;
    this.options = _.merge(DefaultDailyContractUsageClientOptions, options);
  }

  async uploadContractTable(contracts: Contract[]) {
    const uniqueContracts = new UniqueArray<Contract>((c) => c.address);
    contracts.forEach((c) => uniqueContracts.push(c));
    const sortedUniqueContracts = uniqueContracts.items();

    console.log(`SORTED UNIQUE COUNT: ${sortedUniqueContracts.length}`);
    // Sort by creation
    sortedUniqueContracts.sort((a, b) => a.id - b.id);

    const rows = ["id,address"];
    rows.push(
      ...sortedUniqueContracts.map((a) => {
        return `${a.id},${a.address}`;
      }),
    );
    const artifactsCsv = rows.join("\n");

    const contractsCsvSha1 = sha1FromArray([artifactsCsv]);
    console.log(`sha1=${contractsCsvSha1}`);

    logger.debug("about to upload contracts table to dune");
    logger.debug(`sha1=${contractsCsvSha1}`);
    logger.debug(`count=${sortedUniqueContracts.length}`);

    const tableName = `oso_optimism_contracts_${contractsCsvSha1}`;

    const response = await this.uploader.upload(
      tableName,
      `OSO monitored optimism contracts: ${contractsCsvSha1}.`,
      rows,
    );
    if (response.status !== 200) {
      throw new Error("failed to upload contracts table to dune");
    }
    logger.debug(`uploaded to ${tableName}`);
    return contractsCsvSha1;
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
    contractTableReference: ContractTableReference,
  ): Promise<DailyContractUsageRow[]> {
    let contractSha1 = contractTableReference.tableId;
    let contractsMap: Record<number, string> = {};
    if (!contractSha1) {
      if (!contractTableReference.contracts) {
        throw new Error(
          "contracts have not been specified. cannot complete query",
        );
      }
      const contracts = contractTableReference.contracts;
      // If the sha1 isn't set we will upload our own table;
      contractSha1 = await this.uploadContractTable(contracts);
      contractsMap = contracts.reduce<Record<number, string>>((a, c) => {
        a[c.id] = c.address;
        return a;
      }, {});
    } else {
      // Load the contracts table
      contractsMap = await this.loadContractsTable(contractSha1);
    }

    const parameters = [
      QueryParameter.text(
        "start_time",
        range.startDate.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
      ),
      QueryParameter.text(
        "end_time",
        range.endDate.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
      ),
      QueryParameter.text("contracts_table", contractSha1),
    ];

    logger.debug("loading from dune");
    const response = await this.client.refresh(
      this.options.queryId,
      parameters,
    );
    //const response = JSON.parse(await readFile('tester-123456.json', { encoding: 'utf-8' })) as Awaited<ReturnType<IDuneClient["refresh"]>>;
    //await writeFile('tester-123456.json', JSON.stringify(response));
    const rawRows = response.result?.rows as unknown[] as DuneRawRow[];

    // Split raw rows by date
    const rowsByDay = rawRows.reduce<Record<string, DuneRawRow[]>>(
      (acc, curr) => {
        // Update the date value to be ISO
        const rowsForDate = acc[curr.date] || [];
        rowsForDate.push(curr);
        acc[curr.date] = rowsForDate;
        return acc;
      },
      {},
    );

    const sortedDates = Object.keys(rowsByDay).sort();
    const rows: DailyContractUsageRow[] = [];
    for (const date of sortedDates) {
      const rawRows = rowsByDay[date];
      rows.push(...this.expandRowsForDate(contractsMap, rawRows));
    }

    // Aggregate safes. Not sure why but sometimes the data isn't being
    // aggregated on the Dune side.
    return rows;
  }

  expandRowsForDate(
    contractsMap: Record<number, string>,
    rawRows: DuneRawRow[],
  ): DailyContractUsageRow[] {
    const usageRows: DailyContractUsageRow[] = [];

    const safes: Record<string, SafeAggregate> = {};
    for (const rawRow of rawRows) {
      let expandedRows: DailyContractUsageRow[] = [];
      try {
        expandedRows = transformDuneRawRowToUsageRows(rawRow, contractsMap);
      } catch (err) {
        logger.error("Error collecting dune rows", err);
        throw err;
      }
      for (const usageRow of expandedRows) {
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

  // At this time the `_contractSha1` is not needed because the available csvs already resolve the contract addresses
  async getDailyContractUsageFromCsv(
    date: DateTime,
  ): Promise<DailyContractUsageRow[]> {
    return this.loadCsvPath(
      `${this.options.csvDirPath}/${date.toISODate()}.csv`,
    );
  }

  async loadContractsTable(sha: string): Promise<Record<number, string>> {
    const contracts = await loadContractsTable(
      path.join(this.options.tablesDirectoryPath, `contracts-${sha}.csv`),
    );

    return contracts.reduce<Record<number, string>>((acc, curr) => {
      const id = parseInt(curr.id);
      acc[id] = curr.address;
      return acc;
    }, {});
  }

  async loadCsvPath(path: string) {
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
              l2GasUsed: chunk[4],
              l1GasUsed: chunk[5],
              txCount: stringToInt(chunk[6]),
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
