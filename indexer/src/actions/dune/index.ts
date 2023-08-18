import {
  QueryParameter,
  DuneClient,
  ResultsResponse,
} from "@cowprotocol/ts-dune-client";
import { DateTime, Duration } from "luxon";
import {
  getKnownUserAddressesWithinTimeFrame,
  getUnsyncedContracts,
} from "../../db/contracts.js";
import { CommonArgs } from "../../utils/api.js";
import { logger } from "../../utils/logger.js";
import {
  EventType,
  Prisma,
  PrismaClient,
  ContributorNamespace,
  ArtifactNamespace,
  ArtifactType,
} from "@prisma/client";
import { DUNE_API_KEY } from "../../config.js";
import { fstat, readFileSync, writeFileSync } from "fs";
import fsPromises from "fs/promises";
import fs from "fs";
import path from "path";
import { prisma as prismaClient } from "../../db/prisma-client.js";
import { IDuneClient, NoopDuneClient } from "../../utils/dune/type.js";
import _, { add } from "lodash";

const ADDRESS_PAGE_SIZE = 5000;
const MAX_PAGES = 1;

/**
 * Entrypoint arguments
 */
export type ImportDailyContractUsage = CommonArgs & {
  skipExisting?: boolean;
};

export interface DailyContractUsageSyncerOptions {
  // The number of days to sync. More days is more efficient use of API credits
  // within dune. However, we will likely need to set larger datapoint limits
  // per response for many days
  intervalLengthInDays: number;

  // To ensure we only get complete data we should not index 2 days prior to today.
  offsetDays: number;

  // The date to use for sync calculations. Defaults to today. For now this is
  // fairly dumb and we assume the baseDate is today when doing the start/end
  // time calculations for the query.
  baseDate: DateTime;

  // A cache directory for responses which will be used by github actions to
  // load any response we get from a previous run (tbd). This will hopefully
  // reduce our API credit usage within dune
  cacheDirectory: string;

  // The query id in dune to call. The default is below
  contractUsersQueryId: number;
}

export const DefaultDailyContractUsageSyncerOptions: DailyContractUsageSyncerOptions =
  {
    intervalLengthInDays: 7,
    offsetDays: 2,
    cacheDirectory: "",

    // By default we want to sync today
    baseDate: DateTime.now(),

    // This default is based on this: https://dune.com/queries/2835126
    contractUsersQueryId: 2835126,
  };

interface DailyContractUsageRawRow {
  date: string;
  contract_id: number;
  user_addresses: string[] | null;
  user_ids: number[] | null;
  contract_total_l2_gas_cost_gwei: string;
  contract_total_tx_count: number;
}

export interface DailyContractUsageRow {
  date: Date;
  contractAddress: string;
  userAddresses: string[];
  contractTotalL2GasCostGwei: string;
  contractTotalTxCount: number;
}

export class DailyContractUsageCacheableResponse {
  results: ResultsResponse;
  monitoredContracts: Awaited<ReturnType<typeof getUnsyncedContracts>>;
  knownUserAddresses: Awaited<
    ReturnType<typeof getKnownUserAddressesWithinTimeFrame>
  >;

  public static async fromJSON(path: string) {
    const rawResponse = await fsPromises.readFile(path, {
      encoding: "utf-8",
    });
    const parsedResponse = JSON.parse(rawResponse) as {
      results: ResultsResponse;
      monitoredContracts: Awaited<ReturnType<typeof getUnsyncedContracts>>;
      knownUserAddresses: Awaited<
        ReturnType<typeof getKnownUserAddressesWithinTimeFrame>
      >;
    };

    if (parsedResponse.knownUserAddresses.length === 0) {
      // temp
      const usersRaw = await fsPromises.readFile("users0_short.json", {
        encoding: "utf-8",
      });
      const users = JSON.parse(usersRaw) as Array<[string, string]>;
      parsedResponse.knownUserAddresses = users.map((u) => {
        return {
          id: parseInt(u[0]),
          name: u[1],
        };
      });
    }
    return new DailyContractUsageCacheableResponse(
      parsedResponse.results,
      parsedResponse.monitoredContracts,
      parsedResponse.knownUserAddresses,
    );
  }

  constructor(
    results: ResultsResponse,
    monitoredContracts: Awaited<ReturnType<typeof getUnsyncedContracts>>,
    knownUserAddresses: Awaited<
      ReturnType<typeof getKnownUserAddressesWithinTimeFrame>
    >,
  ) {
    this.results = results;
    this.monitoredContracts = monitoredContracts;
    this.knownUserAddresses = knownUserAddresses;
  }

  *rows(): IterableIterator<DailyContractUsageRow> {
    const userAddressMap: { [id: string]: string } = {};
    const contractAddressMap: { [id: string]: string } = {};
    this.monitoredContracts.forEach((c) => {
      contractAddressMap[c.id] = c.name;
    });
    this.knownUserAddresses.forEach((u) => {
      userAddressMap[u.id] = u.name;
    });
    const rows = (this.results.result?.rows || []) as unknown[];
    const processedRows: DailyContractUsageRow[] = [];
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i] as DailyContractUsageRawRow;
      // resolve the user addresses to contract addresses
      const userIds = row.user_ids || [];
      const partialUserAddresses = row.user_addresses || [];
      const contractAddress = contractAddressMap[row.contract_id];
      const userAddresses = userIds
        .map((u) => {
          const addr = userAddressMap[u];
          if (addr === undefined || addr === null) {
            logger.error(`error looking up ${addr} in the given response`);
          }
          return userAddressMap[u];
        })
        .concat(partialUserAddresses);
      console.log(
        `processing ${contractAddress} with ${userAddresses.length} users`,
      );

      yield {
        date: DateTime.fromSQL(row.date).toJSDate(),
        contractAddress: contractAddress,
        userAddresses: userAddresses,
        contractTotalL2GasCostGwei: row.contract_total_l2_gas_cost_gwei,
        contractTotalTxCount: row.contract_total_tx_count,
      };
    }
  }

  toJSON(): string {
    return JSON.stringify({
      results: this.results,
      monitoredContracts: this.monitoredContracts,
      knownUserAddresses: this.knownUserAddresses,
    });
  }
}

export class DailyContractUsageSyncer {
  private client: IDuneClient;
  private prisma: PrismaClient;
  private options: DailyContractUsageSyncerOptions;

  constructor(
    client: IDuneClient,
    prisma: PrismaClient,
    options: Partial<DailyContractUsageSyncerOptions> = DefaultDailyContractUsageSyncerOptions,
  ) {
    this.client = client;
    this.prisma = prisma;
    this.options = {
      ...DefaultDailyContractUsageSyncerOptions,
      ...options,
    };
  }

  async run() {
    // Load the data for a given interval (it might load from cache)
    logger.info("loading contract usage data");
    const usageData = await this.loadData();

    // This is jank... but leave this here for now so we don't duplicate efforts
    // if we encounter addresses multiple times.
    const upsertedAddresses: { [address: string]: number } = {};

    // Get all of the contract address ids based on their address. We shouldn't
    // necessarily trust the addresses in the potentially cached results
    const contracts = await this.prisma.artifact.findMany({
      where: {
        namespace: ArtifactNamespace.OPTIMISM,
        type: ArtifactType.CONTRACT_ADDRESS,
        name: {
          in: usageData.monitoredContracts.map((c) => c.name),
        },
      },
    });
    console.log(
      `monitored contracts length ${usageData.monitoredContracts.length}`,
    );
    console.log(`contracts length ${contracts.length}`);

    const intersect = _.intersection(
      contracts.map((c) => c.name),
      usageData.monitoredContracts.map((c) => c.name),
    );
    if (intersect.length !== usageData.monitoredContracts.length) {
      throw new Error(
        "Missing some expected contracts in the database. No resolution at the moment",
      );
    }

    const contractAddressToArtifactMap: { [address: string]: number } = {};
    contracts.forEach((c) => {
      contractAddressToArtifactMap[c.name] = c.id;
    });

    // Create any contributors that don't already exist in our database. This
    // will also check the "known values" since the cached data is self
    // contained. This is only allowed for now because we _might_ feed
    // information to this which could be useful if we ever delete the database
    // but keep cached artifacts around. Likely shouldn't do this upsert every
    // time. It seems a bit expensive.
    await Promise.all(
      usageData.knownUserAddresses.map(async (u) => {
        const res = await this.prisma.contributor.upsert({
          where: {
            id: u.id,
          },
          create: {
            name: u.name,
            namespace: ContributorNamespace.EOA_ADDRESS,
            updatedAt: new Date(),
          },
          update: {
            updatedAt: new Date(),
          },
        });
        upsertedAddresses[u.name] = res.id;
        return res;
      }),
    );

    for (const row of usageData.rows()) {
      // Process each row into an event for each user address and contract
      const contractAddress = row.contractAddress;
      for (const userAddress of row.userAddresses) {
        if (userAddress === undefined || userAddress === null) {
          logger.info("unexpectedly undefined user address");
          continue;
        }
        let userAddressContributorId = upsertedAddresses[userAddress];
        if (!userAddressContributorId) {
          const contributor = await this.prisma.contributor.create({
            data: {
              updatedAt: new Date(),
              name: userAddress,
              namespace: ContributorNamespace.EOA_ADDRESS,
            },
          });
          upsertedAddresses[userAddress] = contributor.id;
          userAddressContributorId = contributor.id;
        }
        const contractArtifactId =
          contractAddressToArtifactMap[contractAddress];
        const existingEvents = await this.prisma.event.findMany({
          where: {
            artifactId: contractArtifactId,
            contributorId: userAddressContributorId,
            eventType: EventType.CONTRACT_INVOKED,
            eventTime: row.date,
          },
        });

        // should only be one existing event
        if (existingEvents.length > 1) {
          // TODO: add a more detailed error here and collect the errors
          logger.error(
            "A unexpected and and hard to fix error exists within the contract invocation events",
          );
        } else if (existingEvents.length === 0) {
          await this.prisma.event.create({
            data: {
              eventTime: row.date,
              amount: row.contractTotalTxCount,
              eventType: EventType.CONTRACT_INVOKED,
              artifactId: contractAddressToArtifactMap[contractAddress],
              contributorId: userAddressContributorId,
              details: {
                totalL2GasCostGwei: row.contractTotalL2GasCostGwei,
              },
            },
          });
        }
      }
    }

    // Update all event pointers
    // FIXME: For now this doesn't do much error checking... this should be addressed
    await Promise.all(
      usageData.monitoredContracts.map(async (c) => {
        const updatedAt = this.options.baseDate.toJSDate();
        return await this.prisma.eventPointer.upsert({
          where: {
            artifactId_eventType: {
              artifactId: c.id,
              eventType: EventType.CONTRACT_INVOKED,
            },
          },
          create: {
            updatedAt: updatedAt,
            artifactId: c.id,
            eventType: EventType.CONTRACT_INVOKED,
            pointer: {},
            autocrawl: true,
          },
          update: {
            updatedAt: updatedAt,
          },
        });
      }),
    );
  }

  // Load contract usage for the given interval
  protected async loadData(): Promise<DailyContractUsageCacheableResponse> {
    // Check the cache directory for the dune request's cache. We need
    // caching because the API for dune is quiet resource constrained.
    const cache = await this.loadFromCache();
    if (cache) {
      logger.info("loaded data from cache");
      return cache;
    }
    const monitoredContracts = await getUnsyncedContracts(
      this.prisma,
      this.options.baseDate,
    );
    const knownUserAddresses = await getKnownUserAddressesWithinTimeFrame(
      this.prisma,
      this.startDate,
      this.endDate,
      ADDRESS_PAGE_SIZE,
    );
    const parameters = [
      QueryParameter.text(
        "contract_addresses",
        monitoredContracts.map((c) => `(${c.id}, ${c.name})`).join(","),
      ),
      QueryParameter.text(
        "known_user_addresses",
        knownUserAddresses.map((a) => `(${a.id}, ${a.name})`).join(","),
      ),
      QueryParameter.text(
        "start_time",
        this.startDate.toFormat("yyyy-MM-dd 00:00:00 UTC"),
      ),
      QueryParameter.text(
        "end_time",
        this.endDate.toFormat("yyyy-MM-dd 00:00:00 UTC"),
      ),
    ];
    const results = await this.client.refresh(
      this.options.contractUsersQueryId,
      parameters,
    );
    const response = new DailyContractUsageCacheableResponse(
      results,
      monitoredContracts,
      knownUserAddresses,
    );

    // Write this to cache
    await fsPromises.writeFile(this.intervalCachePath(), response.toJSON(), {
      encoding: "utf-8",
    });
    return response;
  }

  protected intervalCachePath() {
    const startDate = this.options.baseDate;
    const intervalLengthInDays: number = this.options.intervalLengthInDays;
    return path.join(
      this.options.cacheDirectory,
      `daily-contract-cache-${startDate.toFormat(
        "yyyy-MM-dd",
      )}-interval-${intervalLengthInDays}.json`,
    );
  }

  protected async loadFromCache(): Promise<
    DailyContractUsageCacheableResponse | undefined
  > {
    const cachePath = this.intervalCachePath();
    logger.info(`attempting to load cache from ${cachePath}`);

    // Check if the cache exists
    try {
      await fsPromises.access(cachePath);
    } catch (err) {
      return;
    }
    return await DailyContractUsageCacheableResponse.fromJSON(cachePath);
  }

  protected get startDate() {
    return this.options.baseDate
      .toUTC()
      .startOf("day")
      .minus(
        Duration.fromObject({
          days: this.options.intervalLengthInDays - this.options.offsetDays,
        }),
      );
  }

  protected get endDate() {
    return this.options.baseDate
      .toUTC()
      .startOf("day")
      .minus(Duration.fromObject({ days: this.options.offsetDays }));
  }
}

export async function importDailyContractUsage(
  args: ImportDailyContractUsage,
): Promise<void> {
  logger.info("importing contract usage");
  //const client = new DuneClient(DUNE_API_KEY);
  const client = new NoopDuneClient();
  const syncer = new DailyContractUsageSyncer(client, prismaClient, {
    cacheDirectory: "/tmp/oso",
  });
  await syncer.run();
  logger.info("done");
}

/*
export async function importDailyContractUsage(
  args: ImportDailyContractUsage,
): Promise<void> {
  logger.info("importing contract usage")
  // Commit each of the completed contract accesses
  const updateDate = DateTime.now().minus(Duration.fromObject({ days: 8 }));
  const contracts = await getUnsyncedContracts(updateDate);
  console.log(`Contracts to sync ${contracts.length}`)

  await Promise.all(contracts.map(async (c) => {
    return await prisma.eventPointer.upsert({
      where: {
        artifactId_eventType: {
          artifactId: c.id,
          eventType: EventType.CONTRACT_INVOKED,
        }
      },
      create: {
        updatedAt: updateDate.toJSDate(),
        artifactId: c.id,
        eventType: EventType.CONTRACT_INVOKED,
        pointer: {},
        autocrawl: true,
      },
      update: {
        updatedAt: updateDate.toJSDate(),
      }
    })
  }));

  /*

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

  logger.info("done");
}

/***/
