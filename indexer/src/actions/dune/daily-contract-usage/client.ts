/**
 * A client for our daily contract usage query on Dune
 *
 * The client will resolve everything in the request to raw addresses as we
 * currently use a method for querying dune that involves passing in
 * known-user-addresses + ids and known-contract-addresses + ids. This reduces
 * the burden of the api calls on our quota by about 20% in testing.
 */
import { DateTime } from "luxon";
import { QueryParameter } from "@cowprotocol/ts-dune-client";
import fsPromises from "fs/promises";

import { UniqueArray } from "../../../utils/array.js";
import { IDuneClient } from "../../../utils/dune/type.js";
import _ from "lodash";

export type DailyContractUsageRawRow = {
  date: string;
  contract_id: number;
  user_addresses: string[] | null;
  user_ids: number[] | null;
  contract_total_l2_gas_cost_gwei: string;
  contract_total_tx_count: number;
  safe_address_count: number;

  // Catch all for other raw values returned in the result
  [key: string]: any;
};

const knownRawData = [
  "date",
  "contract_id",
  "user_addresses",
  "user_ids",
  "contract_total_l2_gas_cost_gwei",
  "contract_total_tx_count",
  "safe_address_count",
];

export type DailyContractUsageRow = {
  date: Date;
  contractAddress: string;
  userAddresses: string[];
  contractTotalL2GasCostGwei: string;
  contractTotalTxCount: number;
  uniqueSafeAddressCount: number;

  // Catch all for other raw values returned in the result
  [key: string]: any;
};

export interface IDailyContractUsageClient {
  getDailyContractUsage(
    start: DateTime,
    end: DateTime,
    knownUserAddresses: string[],
    knownContractAddresses: string[],
  ): Promise<DailyContractUsageRow[]>;
}

export interface DailyContractUsageClientOptions {
  queryId: number;

  // if the max known input for the dune endpoint is reached we will split the
  // contract calls into batches of these sizes.
  contractBatchSize: number;

  // Another guessed number
  maxKnownUsersInput: number;
}

export const DefaultDailyContractUsageClientOptions: DailyContractUsageClientOptions =
  {
    // This default is based on this: https://dune.com/queries/2835126
    queryId: 2835126,

    contractBatchSize: 12000,

    // This number is currently being guessed. That's what we've been able to
    // achieve so far
    maxKnownUsersInput: 5000,
  };

export interface IdToAddressMap {
  [id: number]: string;
}

export type Addresses = string[];

type ContractAddressBatch = {
  map: IdToAddressMap;
  input: string[];
};

/**
 * Mostly a private function but this should be exported so it can both be
 * tested but also used by other things in the future
 */
export function resolveDailyContractUsage(
  userIdToAddressMap: IdToAddressMap,
  contractIdToAddressMap: IdToAddressMap,
  rows: unknown[],
): DailyContractUsageRow[] {
  return rows.map((r) => {
    const row = r as DailyContractUsageRawRow;

    // resolve the user addresses to contract addresses
    const userIds = row.user_ids || [];
    const resolvedAddresses = userIds.map((userId) => {
      const addr = userIdToAddressMap[userId];
      if (!addr) {
        throw new Error(
          "fatal error. user address mapping has unexpected result",
        );
      }
      return addr;
    });

    const contractAddress = contractIdToAddressMap[row.contract_id];
    if (!contractAddress) {
      throw new Error(
        "fatal error. contract address mapping has unexpected result",
      );
    }

    const userAddresses = [...(row.user_addresses || []), ...resolvedAddresses];

    const response: DailyContractUsageRow = {
      date: DateTime.fromSQL(row.date).toJSDate(),
      contractAddress: contractAddress,
      userAddresses: userAddresses,
      contractTotalL2GasCostGwei: row.contract_total_l2_gas_cost_gwei,
      contractTotalTxCount: row.contract_total_tx_count,
      uniqueSafeAddressCount: row.safe_address_count,
    };

    // Copy any extra data so we can save it for later if needed
    Object.keys(row)
      .filter((name) => knownRawData.indexOf(name) === -1)
      .forEach((name) => {
        response[name] = row[name];
      });

    return response;
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

export class DailyContractUsageClient implements IDailyContractUsageClient {
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
  async getDailyContractUsage(
    start: DateTime,
    end: DateTime,
    knownUserAddresses: string[],
    knownContractAddresses: string[],
  ): Promise<DailyContractUsageRow[]> {
    const userIdToAddress: { [id: number]: string } = {};

    const knownUserAddressesInput = knownUserAddresses
      .slice(0, this.options.maxKnownUsersInput)
      .map((addr, i) => {
        userIdToAddress[i] = addr;
        return `(${i}, ${addr})`;
      })
      .join(",");

    const contractBatches = this.contractAddressesToBatch(
      knownContractAddresses,
    );
    let rows: DailyContractUsageRow[] = [];

    for (const batch of contractBatches) {
      const parameters = [
        QueryParameter.text("contract_addresses", batch.input.join(",")),
        QueryParameter.text("known_user_addresses", knownUserAddressesInput),
        QueryParameter.text(
          "start_time",
          start.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
        ),
        QueryParameter.text(
          "end_time",
          end.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
        ),
      ];
      const response = await this.client.refresh(
        this.options.queryId,
        parameters,
      );
      rows = rows.concat(
        resolveDailyContractUsage(
          userIdToAddress,
          batch.map,
          response.result?.rows || [],
        ),
      );
    }

    return rows;
  }

  private contractAddressesToBatch(
    addresses: string[],
  ): ContractAddressBatch[] {
    const batches: ContractAddressBatch[] = [];
    const size = this.options.contractBatchSize;
    for (let i = 0; i < addresses.length; i += size) {
      const batchAddrs = addresses.slice(i, i + size);
      const map: ContractAddressBatch["map"] = {};
      const input = batchAddrs.map((addr, j) => {
        map[j] = addr;
        return `(${j}, ${addr})`;
      });

      batches.push({
        map: map,
        input: input,
      });
    }
    return batches;
  }
}

interface DailyContractUsageResponseRaw {
  rows: DailyContractUsageRow[];
  input: {
    contractAddresses: string[];
  };
}

type CachedDailyContractUsageResponse = Omit<
  DailyContractUsageResponseRaw,
  "rows"
> & {
  rows: CachedDailyContractUsageRow[];
};

type CachedDailyContractUsageRow = Omit<DailyContractUsageRow, "date"> & {
  date: string;
};

export class DailyContractUsageResponse {
  // The daily contract usage responses from dune are queried with mappings of
  // all of our contracts that we monitor and their associated ids and some
  // number of the top users. The difficulty is that we have limited quota from
  // Dune so in case we delete our database and start over again we need to
  // store exactly the id mapping we used so that we can consistently restore
  // this data (especially while we're still building the system). This
  // cacheable response allows for this.

  private rows: DailyContractUsageRow[];
  private _contractAddresses: string[];

  private memoUniqueUserAddresses: UniqueArray<string>;
  private memoRowsByContract: {
    [contract: string]: DailyContractUsageRow[];
  };

  private processed: boolean;

  public static async fromJSON(path: string) {
    const raw = await fsPromises.readFile(path, {
      encoding: "utf-8",
    });
    const cached = JSON.parse(raw) as CachedDailyContractUsageResponse;
    const rows: DailyContractUsageRow[] = cached.rows.map((a) => {
      return {
        ...a,
        ...{ date: DateTime.fromISO(a.date).toJSDate() },
      } as DailyContractUsageRow;
    });

    return new DailyContractUsageResponse(rows, cached.input.contractAddresses);
  }

  constructor(rows: DailyContractUsageRow[], contractAddresses: string[]) {
    this.rows = rows;
    this._contractAddresses = contractAddresses;
    this.processed = false;
    this.memoUniqueUserAddresses = new UniqueArray((a) => a);
    this.memoRowsByContract = {};
  }

  // Process the rows so we can:
  //   * resolve the userIds in the response to addresses.
  //   * get a list of user addresses (known and unknown)
  private processRows() {
    this.rows.forEach((row) => {
      // resolve the user addresses to contract addresses
      row.userAddresses.forEach((a) => {
        this.memoUniqueUserAddresses.push(a);
      });
      const contractAddressRows =
        this.memoRowsByContract[row.contractAddress] || [];
      contractAddressRows.push(row);
      this.memoRowsByContract[row.contractAddress] = contractAddressRows;
    });
    this.processed = true;
  }

  uniqueUserAddresses(): string[] {
    if (!this.processed) {
      this.processRows();
    }

    return this.memoUniqueUserAddresses.items();
  }

  async mapRowsByContractAddress<R>(
    cb: (contractAddress: string, rows: DailyContractUsageRow[]) => Promise<R>,
    parallelism: number = 20,
  ): Promise<Array<R>> {
    if (!this.processed) {
      this.processRows();
    }

    let result: Array<R> = [];
    let parallel: Array<Promise<R>> = [];

    for (const addr of this.contractAddresses) {
      const rows = this.memoRowsByContract[addr] || [];
      parallel.push(cb(addr, rows));
      if (parallel.length > parallelism) {
        result = result.concat(await Promise.all(parallel));
        parallel = [];
      }
    }
    if (parallel.length > 0) {
      result = result.concat(await Promise.all(parallel));
      await Promise.all(parallel);
    }

    return result;
  }

  toJSON(): string {
    return JSON.stringify({
      rows: this.rows,
      input: {
        contractAddresses: this._contractAddresses,
      },
    } as DailyContractUsageResponseRaw);
  }

  get contractAddresses() {
    return _.clone(this._contractAddresses);
  }
}
