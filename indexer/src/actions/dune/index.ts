import {
  QueryParameter,
  DuneClient,
  ResultsResponse,
} from "@cowprotocol/ts-dune-client";
import { DateTime, Duration } from "luxon";
import {
  getKnownUserAddressesWithinTimeFrame,
  getSyncedContracts,
  getMonitoredContracts,
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
  Event,
  Contributor,
} from "@prisma/client";
import { DUNE_API_KEY } from "../../config.js";
import { fstat, readFileSync, writeFileSync } from "fs";
import fsPromises from "fs/promises";
import fs from "fs";
import path from "path";
import { prisma as prismaClient } from "../../db/prisma-client.js";
import { IDuneClient, NoopDuneClient } from "../../utils/dune/type.js";
import _, { add, identity } from "lodash";
import { error } from "console";

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

class UniqueList<T> {
  private uniqueMap: { [key: string]: boolean };
  private arr: T[];
  private idFunc: (value: T) => string;

  constructor(idFunc: (value: T) => string) {
    this.uniqueMap = {};
    this.arr = [];
    this.idFunc = idFunc;
  }

  push(obj: T) {
    const id = this.idFunc(obj);
    if (this.uniqueMap[id] !== undefined) {
      return this.arr.length;
    }
    this.uniqueMap[id] = true;
    this.arr.push(obj);
  }

  items(): T[] {
    return this.arr;
  }
}

async function loadFakeKnownAddresses() {
  const usersRaw = await fsPromises.readFile("users0_short.json", {
    encoding: "utf-8",
  });
  const users = JSON.parse(usersRaw) as Array<[string, string]>;
  return users.map((u) => {
    return {
      id: parseInt(u[0]),
      name: u[1],
    };
  });
}

export class DailyContractUsageCacheableResponse {
  results: ResultsResponse;
  monitoredContracts: Awaited<ReturnType<typeof getMonitoredContracts>>;
  knownUserAddresses: Awaited<
    ReturnType<typeof getKnownUserAddressesWithinTimeFrame>
  >;

  private processed: boolean;
  private cachedUniqueKnownUserAddresses: UniqueList<string>;
  private cachedUniqueNewUserAddresses: UniqueList<string>;
  private cachedProcessedRowsByContract: {
    [contract: string]: DailyContractUsageRow[];
  };

  public static async fromJSON(path: string) {
    const rawResponse = await fsPromises.readFile(path, {
      encoding: "utf-8",
    });
    const parsedResponse = JSON.parse(rawResponse) as {
      results: ResultsResponse;
      monitoredContracts: Awaited<ReturnType<typeof getMonitoredContracts>>;
      knownUserAddresses: Awaited<
        ReturnType<typeof getKnownUserAddressesWithinTimeFrame>
      >;
    };

    if (parsedResponse.knownUserAddresses.length === 0) {
      // temp
      parsedResponse.knownUserAddresses = await loadFakeKnownAddresses();
    }
    return new DailyContractUsageCacheableResponse(
      parsedResponse.results,
      parsedResponse.monitoredContracts,
      parsedResponse.knownUserAddresses,
    );
  }

  constructor(
    results: ResultsResponse,
    monitoredContracts: Awaited<ReturnType<typeof getMonitoredContracts>>,
    knownUserAddresses: Awaited<
      ReturnType<typeof getKnownUserAddressesWithinTimeFrame>
    >,
  ) {
    this.results = results;
    this.monitoredContracts = monitoredContracts;
    this.knownUserAddresses = knownUserAddresses;
    this.cachedProcessedRowsByContract = {};
    this.processed = false;
    this.cachedUniqueKnownUserAddresses = new UniqueList((a) => a);
    this.cachedUniqueNewUserAddresses = new UniqueList((a) => a);
  }

  // Process the rows so we can:
  //   * resolve the userIds in the response to addresses.
  //   * get a list of user addresses (known and unknown)
  private processRows() {
    logger.info(`what is this heere`);
    const contractAddressMap = this.monitoredContracts.reduce<{
      [id: number]: string;
    }>((cmap, c) => {
      cmap[c.id] = c.name;
      return cmap;
    }, {});

    const userAddressMap = this.knownUserAddresses.reduce<{
      [id: number]: string;
    }>((umap, u) => {
      umap[u.id] = u.name;
      this.cachedUniqueKnownUserAddresses.push(u.name);
      return umap;
    }, {});

    const rows = (this.results.result?.rows || []) as unknown[];
    const processedRows = this.cachedProcessedRowsByContract;

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i] as DailyContractUsageRawRow;
      // resolve the user addresses to contract addresses
      const userIds = row.user_ids || [];
      const partialUserAddresses = row.user_addresses || [];

      // Add new user addresses to the new users hash map
      partialUserAddresses.forEach((a) => {
        this.cachedUniqueNewUserAddresses.push(a);
      });

      const contractAddress = contractAddressMap[row.contract_id];
      const contractAddressRows = processedRows[contractAddress] || [];

      const userAddresses = userIds
        .map((u) => {
          const addr = userAddressMap[u];
          if (addr === undefined || addr === null) {
            logger.error(`error looking up ${u} in the given response`);
            throw new Error("irrecoverable");
          }
          return userAddressMap[u];
        })
        .concat(partialUserAddresses);

      contractAddressRows.push({
        date: DateTime.fromSQL(row.date).toJSDate(),
        contractAddress: contractAddress,
        userAddresses: userAddresses,
        contractTotalL2GasCostGwei: row.contract_total_l2_gas_cost_gwei,
        contractTotalTxCount: row.contract_total_tx_count,
      });
      processedRows[contractAddress] = contractAddressRows;
    }
  }

  uniqueUserAddresses(): string[] {
    if (!this.processed) {
      this.processRows();
    }

    return [
      ...this.cachedUniqueKnownUserAddresses.items(),
      ...this.cachedUniqueNewUserAddresses.items(),
    ];
  }

  mapRowsByContractAddress<R>(
    cb: (contractAddress: string, rows: DailyContractUsageRow[]) => R,
  ): Array<R> {
    if (!this.processed) {
      this.processRows();
    }

    return Object.keys(this.cachedProcessedRowsByContract).map((address) => {
      return cb(address, this.cachedProcessedRowsByContract[address]);
    });
  }

  toJSON(): string {
    return JSON.stringify({
      results: this.results,
      monitoredContracts: this.monitoredContracts,
      knownUserAddresses: this.knownUserAddresses,
    });
  }
}

type DailyContractInvokeEventData = Pick<
  Event,
  "amount" | "eventTime" | "eventType" | "contributorId" | "artifactId"
>;

export class DailyContractUsageSyncer {
  private client: IDuneClient;
  private prisma: PrismaClient;
  private options: DailyContractUsageSyncerOptions;
  private allUsers: Pick<Contributor, "id" | "name" | "namespace">[];
  private addressToUserIdMap: { [address: string]: number };

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
    this.allUsers = [];
    this.addressToUserIdMap = {};
  }

  async run() {
    // Load the data for a given interval (it might load from cache)
    logger.info("loading contract usage data");
    const usageData = await this.loadData();

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

    const intersect = _.intersection(
      contracts.map((c) => c.name),
      usageData.monitoredContracts.map((c) => c.name),
    );
    if (intersect.length !== usageData.monitoredContracts.length) {
      throw new Error(
        "Missing some expected contracts in the database. No resolution at the moment",
      );
    }

    const contractAddressMap: { [address: string]: number } = {};
    contracts.forEach((c) => {
      contractAddressMap[c.name] = c.id;
    });

    const uniqueUserAddresses = usageData.uniqueUserAddresses();

    await this.ensureUsersExist(uniqueUserAddresses);

    // Some of these events may have already been loaded. Let's skip them so we
    // can make this proceses faster. This allows for idempotent runs multiple
    // times on the same cached data.
    const synced = await getSyncedContracts(this.prisma, this.options.baseDate);
    const syncedMap = synced.reduce<{ [addr: string]: boolean }>(
      (lookup, contract) => {
        lookup[contract.name] = true;
        return lookup;
      },
      {},
    );

    logger.info("Add all events by contract address");
    // We can process each address concurrently (although node won't actually do that)
    await Promise.all(
      usageData.mapRowsByContractAddress(async (contractAddress, days) => {
        const contractId = contractAddressMap[contractAddress];
        if (syncedMap[contractAddress]) {
          logger.info(
            `skipping Contract<${contractId}> "${contractAddress}". already synced`,
          );
          return;
        }
        // Create an event that reports the aggregate transaction information with
        // no contributor information

        // Process each day sequentially so we can block on some calls
        for (const day of days) {
          const userIds = day.userAddresses.map((addr) => {
            const id = this.addressToUserId(addr);
            if (!id) {
              throw new Error(`missing id for ${addr}`);
            }
            return id;
          });

          // Check which users already have data written for that day.
          // We'll need to update those
          const existingEvents = await this.prisma.event.findMany({
            where: {
              eventTime: day.date,
              eventType: EventType.CONTRACT_INVOKED,
              contributorId: {
                in: userIds,
              },
              artifactId: contractId,
            },
          });

          const existingEventsMap: { [id: number]: Array<number> } = {};

          existingEvents.forEach((e) => {
            if (!e.contributorId) {
              return;
            }
            const eventIds = existingEventsMap[e.contributorId] ?? [];
            eventIds.push(e.id);
            existingEventsMap[e.contributorId] = eventIds;
          });

          const tx = userIds
            .map((id) => {
              const data = {
                eventTime: day.date,
                eventType: EventType.CONTRACT_INVOKED,
                contributorId: id,
                artifactId: contractId,
                amount: 0,
              };
              const existingEvents = existingEventsMap[id] || [];
              if (existingEvents.length > 0) {
                if (existingEvents.length > 1) {
                  // FIXME: determine what to do in this instance
                  logger.error(
                    `contract Artifact<${contractId}> has duplicate entries for events related to user address Contributor<${id}> on ${day}`,
                  );
                }
                return this.prisma.event.update({
                  where: {
                    id: existingEvents[0],
                  },
                  data: data,
                });
              }
              return this.prisma.event.create({
                data: data,
              });
            })
            .filter((t) => t !== undefined);

          await this.prisma.$transaction(tx);
        }
        // Update the event pointer for this contract
        // FIXME: For now this doesn't do much error checking... this should be addressed
        const updatedAt = this.options.baseDate.toJSDate();
        return await this.prisma.eventPointer.upsert({
          where: {
            artifactId_eventType: {
              artifactId: contractId,
              eventType: EventType.CONTRACT_INVOKED,
            },
          },
          create: {
            updatedAt: updatedAt,
            artifactId: contractId,
            eventType: EventType.CONTRACT_INVOKED,
            pointer: {},
            autocrawl: false,
          },
          update: {
            updatedAt: updatedAt,
          },
        });
      }),
    );
  }

  protected async loadAllUsers() {
    this.allUsers = await this.prisma.contributor.findMany({
      select: {
        id: true,
        name: true,
        namespace: true,
      },
      where: {
        namespace: ContributorNamespace.EOA_ADDRESS,
      },
    });

    this.addressToUserIdMap = this.allUsers.reduce<{ [addr: string]: number }>(
      (map, u) => {
        map[u.name] = u.id;
        return map;
      },
      {},
    );
  }

  protected addressToUserId(address: string): number {
    return this.addressToUserIdMap[address];
  }

  protected async ensureUsersExist(addresses: string[]) {
    logger.info("Add any new users for this time period");
    // Load all the currently known users
    await this.loadAllUsers();
    const existingAddresses = this.allUsers.map((u) => {
      return u.name;
    });
    const addressesToAdd = _.difference(addresses, existingAddresses);

    // Query for all users in the response data so we can insert any that do not
    // exist
    let batch = [];

    for (const addr of addressesToAdd) {
      batch.push(
        this.prisma.contributor.upsert({
          where: {
            name_namespace: {
              namespace: ContributorNamespace.EOA_ADDRESS,
              name: addr,
            },
          },
          create: {
            name: addr,
            namespace: ContributorNamespace.EOA_ADDRESS,
          },
          update: {},
        }),
      );
      if (batch.length > 20000) {
        logger.info("batching user upserts");
        await this.prisma.$transaction(batch);
        batch = [];
      }
    }
    if (batch.length > 0) {
      await this.prisma.$transaction(batch);
    }

    await this.loadAllUsers();
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
    const monitoredContracts = await getMonitoredContracts(this.prisma);
    const knownUserAddresses = await loadFakeKnownAddresses();
    /*
    const knownUserAddresses = await getKnownUserAddressesWithinTimeFrame(
      this.prisma,
      this.startDate,
      this.endDate,
      ADDRESS_PAGE_SIZE,
    );
    */
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
