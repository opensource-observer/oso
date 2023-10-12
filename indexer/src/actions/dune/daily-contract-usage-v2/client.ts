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
  getDailyContractUsage(date: DateTime): Promise<DailyContractUsageRow[]>;
}

export interface DailyContractUsageClientOptions {
  queryId: number;

  // if the max known input for the dune endpoint is reached we will split the
  // contract calls into batches of these sizes.
  contractBatchSize: number;

  // Another guessed number
  maxKnownUsersInput: number;

  // Load from CSV Path
  csvPath: string;
}

export const DefaultDailyContractUsageClientOptions: DailyContractUsageClientOptions =
  {
    // This default is based on this: https://dune.com/queries/2835126
    queryId: 2835126,

    contractBatchSize: 12000,

    // This number is currently being guessed. That's what we've been able to
    // achieve so far
    maxKnownUsersInput: 5000,

    csvPath: "",
  };

export interface IdToAddressMap {
  [id: number]: string;
}

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
    options: DailyContractUsageClientOptions = DefaultDailyContractUsageClientOptions,
  ) {
    this.client = client;
    this.options = options;
  }

  /**
   * Refreshes our dune [query](https://dune.com/queries/2835126) to resolve the
   * daily contract usage. This accepts only strings of addresses for the known
   * users and known contracts so as to stay agnostic from the state of the
   * database at the current time. We can then store the results (after
   * unmapping returned ids to addresses) and reuse them if the database needs
   * to be rebuilt from scratch. The known user addresses are expected to be in
   * descending order of the most active addresses.
   *
   * @param start
   * @param end
   * @param knownUserAddresses
   * @param knownContractAddresses
   */
  getDailyContractUsage(
    date: DateTime,
    //_contractSha1: string = "da1aae77b853fc7c74038ee08eec441b10b89570",
  ): Promise<DailyContractUsageRow[]> {
    return this.loadCsvPath(
      `/data/tmp/oso/dune-backfill/${date.toISODate()}.csv`,
    );
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
