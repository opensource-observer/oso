import {
  QueryParameter,
  DuneClient,
  ResultsResponse,
} from "@cowprotocol/ts-dune-client";
import { DateTime, Duration } from "luxon";
import { getUnsyncedContracts } from "../../db/contracts.js";
import { CommonArgs } from "../../utils/api.js";
import { logger } from "../../utils/logger.js";
import { DUNE_API_KEY } from "../../config.js";
import { fstat, readFileSync, writeFileSync } from "fs";
import fsPromises from "fs/promises";
import fs from "fs";
import path from "path";

const QUERY_ID = 2835126;
const ADDRESS_PAGE_SIZE = 5000;
const MAX_PAGES = 1;

/**
 * Entrypoint arguments
 */
export type ImportDailyContractUsage = CommonArgs & {
  skipExisting?: boolean;
};

export interface DailyContractUsageSyncerOptions {
  intervalLengthInDays: number;
  cacheDirectory: string;
  startDate: DateTime;
}

const DEFAULT_OPTIONS: DailyContractUsageSyncerOptions = {
  intervalLengthInDays: 7,
  cacheDirectory: "",
  startDate: DateTime.now(),
};

export interface DailyContractUsageCachedResponse {
  results: ResultsResponse;
  monitoredContracts: Awaited<ReturnType<typeof getUnsyncedContracts>>;
  knownAddresses: { id: string; address: string }[];
}

export class DailyContractUsageSyncer {
  private client: DuneClient;
  private options: DailyContractUsageSyncerOptions;

  constructor(
    client: DuneClient,
    options: DailyContractUsageSyncerOptions = DEFAULT_OPTIONS,
  ) {
    this.client = client;
    this.options = options;
  }

  // Load contract usage for the given interval
  async loadForInterval() {
    // Check the cache directory for the dune request's cache. We need
    // caching because the API for dune is quiet resource constrained.
    /*
        const cache = await this.loadFromCache();
        let monitoredContracts = cache?.monitoredContracts || [];
        let knownAddresses = cache
        if (!cache) {
            const intervalLengthInDays: number = this.options.intervalLengthInDays;
        }
        // 
        /**/
  }

  private intervalCachePath() {
    const startDate = this.options.startDate;
    const intervalLengthInDays: number = this.options.intervalLengthInDays;
    return path.join(
      this.options.cacheDirectory,
      `daily-contract-cache-${startDate.toFormat(
        "yyyy-MM-dd",
      )}-interval-${intervalLengthInDays}.json`,
    );
  }

  private async loadFromCache(): Promise<
    DailyContractUsageCachedResponse | undefined
  > {
    const cachePath = this.intervalCachePath();

    // Check if the cache exists
    try {
      await fsPromises.access(cachePath);
    } catch {
      return;
    }

    const rawResponse = await fsPromises.readFile(cachePath, {
      encoding: "utf-8",
    });
    return JSON.parse(rawResponse) as DailyContractUsageCachedResponse;
  }
}

export async function importDailyContractUsage(
  args: ImportDailyContractUsage,
): Promise<void> {
  /*
    logger.info("importing contract usage")
    // Commit each of the completed contract accesses
    const contracts = await getUnsyncedContracts(new Date())

    const now = DateTime.utc();
    const startDate = now.minus(Duration.fromObject({ days: 8 }));
    const endDate = now.minus(Duration.fromObject({ days: 1 }));

    console.log(`Contracts to load ${contracts.length}`);

    const results = readFileSync('results.json', 'utf-8');
    const parsed = JSON.parse(results) as ResultsResponse;

    console.log(`length of results from previous run ${parsed.result?.rows.length}`);
    const uniqueAddressesLookup: { [add: string]: number } = {};
    const dates: { [d: string]: number } = {};
    let uniqueAddressesCount = 0;
    parsed.result?.rows.forEach((r) => {
        const addresses = r.user_addresses as string[];
        const date = r.date as string
        if (!dates[date]) {
            dates[date] = 1;
        } else {
            dates[date] += 1;
        }
        addresses.forEach((a) => {
            if (!uniqueAddressesLookup[a]) {
                uniqueAddressesLookup[a] = 1;
                uniqueAddressesCount += 1;
            } else {
                uniqueAddressesLookup[a] += 1;
            }
        });
    });
    let pairs = Object.keys(uniqueAddressesLookup).map((k) => [uniqueAddressesLookup[k], k]) as Array<[number, string]>;
    pairs.sort((a, b) => a[0] - b[0]);
    pairs.reverse();

    let addressPages: Array<string> = [];
    for (let p = 0; p < MAX_PAGES; p++) {
        const startOffset = p * ADDRESS_PAGE_SIZE;
        if (startOffset > pairs.length) {
            break;
        }
        addressPages.push(
            pairs.slice(startOffset, startOffset + ADDRESS_PAGE_SIZE).map((a, i) => `(${i + startOffset}, ${a[1]})`).join(',')
        );


        writeFileSync(`users${p}_short.txt`, addressPages[p]);
    }

    const orderedContracts = contracts.map((c) => `(${c.id}, ${c.name})`).sort();
    const chunkSize = 20000;
    let chunk = 0;
    while (chunk * chunkSize < orderedContracts.length) {
        const start = chunk * chunkSize;
        const end = start + chunkSize;
        const contractSlice = orderedContracts.slice(start, end);
        writeFileSync(`contracts${chunk}.txt`, contractSlice.join(','));
        chunk += 1;
    }
    let parameters = [
        QueryParameter.text('addresses', contracts.map((c) => `(${c.id}, ${c.name})`).join(',')),
        //QueryParameter.text('start_time', startDate.toFormat('yyyy-MM-dd 00:00:00') + ' UTC'),
        //QueryParameter.text('end_time', endDate.toFormat('yyyy-MM-dd 00:00:00') + ' UTC'),
        QueryParameter.text('start_time', '2023-08-07 00:00:00 UTC'),
        QueryParameter.text('end_time', '2023-08-14 00:00:00 UTC'),
    ];
    addressPages.forEach((page, i) => {
        parameters.push(QueryParameter.text(`known_users_addresses`, page));
    });
    console.log(dates);

    const client = new DuneClient(DUNE_API_KEY);
    const res = await client.refresh(QUERY_ID, parameters);

    console.log(`Job ID: ${res.execution_id}`);
    console.log(`Job Rows: ${res.result?.rows.length}`);

    let completed = [];

    writeFileSync('results-all-transactions-including-safes-count.json', JSON.stringify(res));

    // const rows = res.result?.rows || [];
    // for(let i = 0; i < rows.length; i++) {
    //     rows
    //}
    /***/

  logger.info("done");
}

export async function loadContracts() {}
