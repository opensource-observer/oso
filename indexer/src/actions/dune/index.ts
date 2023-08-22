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
  PrismaClient,
  ContributorNamespace,
  Contributor,
} from "@prisma/client";
import { DUNE_API_KEY } from "../../config.js";
import fsPromises from "fs/promises";
import path from "path";
import { prisma as prismaClient } from "../../db/prisma-client.js";
import { IDuneClient } from "../../utils/dune/type.js";
import _ from "lodash";

const MAX_KNOWN_ADDRESSES = 5000;

/**
 * Entrypoint arguments
 */
export type ImportDailyContractUsage = CommonArgs & {
  skipExisting?: boolean;
  baseDate?: DateTime;
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
  safe_address_count: number;
}

export interface DailyContractUsageRow {
  date: Date;
  contractAddress: string;
  userAddresses: string[];
  contractTotalL2GasCostGwei: string;
  contractTotalTxCount: number;
  uniqueSafeAddressCount: number;
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

export class DailyContractUsageCacheableResponse {
  // The daily contract usage responses from dune are queried with mappings of
  // all of our contracts that we monitor and their associated ids and some
  // number of the top users. The difficulty is that we have limited quota from
  // Dune so in case we delete our database and start over again we need to
  // store exactly the id mapping we used so that we can consistently restore
  // this data (especially while we're still building the system). This
  // cacheable response allows for this.

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
    logger.debug(
      "Processing rows in retrieved daily usage data to map ids to addresses",
    );

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
        uniqueSafeAddressCount: row.safe_address_count,
      });
      processedRows[contractAddress] = contractAddressRows;
    }
    this.processed = true;
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

export class DailyContractUsageSyncer {
  private client: IDuneClient;
  private prisma: PrismaClient;
  private options: DailyContractUsageSyncerOptions;
  private allUsers: Pick<Contributor, "id" | "name" | "namespace">[];
  private userAddressToIdMap: { [address: string]: number };
  private contractsAlreadySynced: { [address: string]: boolean };
  private contracts: Awaited<ReturnType<typeof getMonitoredContracts>>;
  private contractAddressToIdMap: { [address: string]: number };

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
    this.userAddressToIdMap = {};
    this.contractsAlreadySynced = {};
    this.contracts = [];
    this.contractAddressToIdMap = {};
  }

  async run() {
    await this.loadSystemState();

    // Retrieve the data for a given interval (it might load from cache)
    logger.info("loading contract usage data");
    const usageData = await this.retrieveUsageData();

    const uniqueUserAddresses = usageData.uniqueUserAddresses();
    await this.ensureUsersExist(uniqueUserAddresses);

    logger.info("Add all events by contract address");
    await Promise.all(
      usageData.mapRowsByContractAddress(async (contractAddress, days) => {
        const contractId = this.contractAddressToId(contractAddress);
        if (this.isContractSynced(contractAddress)) {
          logger.info(
            `skipping Contract<${contractId}> "${contractAddress}". already synced`,
          );
          return;
        }
        // Process each day sequentially so we can block on each day's transactions
        for (const day of days) {
          await this.createEventsForDay(contractId, day);
          logger.debug(
            `added events for Contract<${contractId}>(${contractAddress}) on ${DateTime.fromJSDate(
              day.date,
            ).toFormat("yyyy-MM-dd")}`,
          );
        }

        // Update the event pointer for this contract
        // FIXME: For now this doesn't do much error checking... this should be addressed
        const updatedAt = this.options.baseDate.toJSDate();

        await this.prisma.eventPointer.upsert({
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
        logger.debug(
          `updated all events for Contract<${contractId}>(${contractAddress}) for ${this.startDate.toFormat(
            "yyyy-MM-dd",
          )} to ${this.endDate.toFormat("yyyy-MM-dd")}`,
        );
      }),
    );
  }

  protected get startDate() {
    return this.options.baseDate
      .toUTC()
      .startOf("day")
      .minus(
        Duration.fromObject({
          days: this.options.intervalLengthInDays + this.options.offsetDays,
        }),
      );
  }

  protected get endDate() {
    return this.options.baseDate
      .toUTC()
      .startOf("day")
      .minus(Duration.fromObject({ days: this.options.offsetDays }));
  }

  protected async loadSystemState() {
    // Loads the system state into memory (this won't scale indefinitely but
    // likely for a while) so that we can quickly process information without
    // having to do too many db requests to do mapping. This is a tradeoff
    // between storing users and contract addresses in the database such that it
    // can stored more efficiently. For now this should be fine.

    // Load contracts we monitor
    await this.loadAllContracts();

    // Load all the users we have in the database
    await this.loadAllUsers();

    // Load a mapping of all the already synced contracts
    await this.loadSyncedContracts();
  }

  protected async loadAllContracts() {
    this.contracts = await getMonitoredContracts(this.prisma);
    this.contracts.forEach((c) => {
      this.contractAddressToIdMap[c.name] = c.id;
    });
  }

  contractAddressToId(address: string) {
    return this.contractAddressToIdMap[address];
  }

  protected async loadSyncedContracts() {
    // Used to determine if the given contract address is up to date so we can
    // skip it in processing on subsequent runs.
    const synced = await getSyncedContracts(this.prisma, this.options.baseDate);
    this.contractsAlreadySynced = synced.reduce<{ [addr: string]: boolean }>(
      (lookup, contract) => {
        lookup[contract.name] = true;
        return lookup;
      },
      {},
    );
  }

  protected isContractSynced(address: string) {
    return this.contractsAlreadySynced[address];
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

    this.userAddressToIdMap = this.allUsers.reduce<{ [addr: string]: number }>(
      (map, u) => {
        map[u.name] = u.id;
        return map;
      },
      {},
    );
  }

  userAddressToId(address: string): number {
    return this.userAddressToIdMap[address];
  }

  protected async loadKnownAddressesSeed(): Promise<
    { id: number; name: string }[]
  > {
    const knownAddressesSeedPath = path.join(
      this.options.cacheDirectory,
      "known-user-addresses-seed.json",
    );

    const usersRaw = await fsPromises.readFile(knownAddressesSeedPath, {
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

  protected async retrieveUsageData(): Promise<DailyContractUsageCacheableResponse> {
    // Load all necessary sync related data

    // Check the cache directory for the dune request's cache. We need
    // caching because the API for dune is quiet resource constrained.
    let usageData = await this.retrieveFromCache();
    if (usageData) {
      logger.info("loaded data from cache");
      return usageData;
    } else {
      const monitoredContracts = await getMonitoredContracts(this.prisma);
      let knownUserAddresses = await getKnownUserAddressesWithinTimeFrame(
        this.prisma,
        this.startDate,
        this.endDate,
        MAX_KNOWN_ADDRESSES,
      );

      // This is needed because the first time this is run there won't be any known addresses.
      if (knownUserAddresses.length === 0) {
        try {
          knownUserAddresses = await this.loadKnownAddressesSeed();
        } catch (e) {
          throw new Error(
            "this is an expensive call the known addresses seed must be specified if the database contains no known users",
          );
        }
      }

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
          this.startDate.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
        ),
        QueryParameter.text(
          "end_time",
          this.endDate.toFormat("yyyy-MM-dd 00:00:00") + " UTC",
        ),
      ];
      logger.debug(
        `retreiving data for ${this.startDate.toFormat(
          "yyyy-MM-dd 00:00:00 UTC",
        )} to ${this.endDate.toFormat("yyyy-MM-dd 00:00:00 UTC")}`,
      );

      await fsPromises.writeFile(
        "contracts.txt",
        monitoredContracts.map((c) => `(${c.id}, ${c.name})`).join(","),
      );
      await fsPromises.writeFile(
        "users.txt",
        knownUserAddresses.map((a) => `(${a.id}, ${a.name})`).join(","),
      );

      const results = await this.client.refresh(
        this.options.contractUsersQueryId,
        parameters,
      );

      usageData = new DailyContractUsageCacheableResponse(
        results,
        monitoredContracts,
        knownUserAddresses,
      );

      // Write this to cache
      await fsPromises.writeFile(this.intervalCachePath(), usageData.toJSON(), {
        encoding: "utf-8",
      });
    }
    // Validate the given data to process
    this.validateUsageData(usageData);

    return usageData;
  }

  protected async retrieveFromCache(): Promise<
    DailyContractUsageCacheableResponse | undefined
  > {
    // We should try not to duplicate date. This method will choose to use a
    // cache if it falls within the same interval.
    const cachePaths = this.possibleCachePathsWithinInterval();
    let cachePath = "";
    console.log(cachePaths);
    for (const { baseDate, path } of cachePaths) {
      logger.info(`attempting cache from ${path}`);
      try {
        await fsPromises.access(path);
      } catch (err) {
        continue;
      }
      this.options.baseDate = baseDate;
      cachePath = path;
      break;
    }
    if (cachePath === "") {
      return;
    }

    // Check if the cache exists
    return await DailyContractUsageCacheableResponse.fromJSON(cachePath);
  }

  protected possibleCachePathsWithinInterval(): {
    baseDate: DateTime;
    path: string;
  }[] {
    const currentBase = this.options.baseDate;
    const intervalLengthInDays = this.options.intervalLengthInDays;
    const possibleCachePaths: { baseDate: DateTime; path: string }[] = [];
    for (let i = 0; i < intervalLengthInDays; i++) {
      const date = currentBase.minus(Duration.fromObject({ days: i }));
      const path = this.intervalCachePath(date);
      possibleCachePaths.push({
        baseDate: date,
        path: path,
      });
    }
    return possibleCachePaths;
  }

  protected intervalCachePath(date?: DateTime) {
    if (!date) {
      date = this.options.baseDate;
    }
    const intervalLengthInDays = this.options.intervalLengthInDays;
    return path.join(
      this.options.cacheDirectory,
      `daily-contract-cache-${date.toFormat(
        "yyyy-MM-dd",
      )}-interval-${intervalLengthInDays}.json`,
    );
  }

  protected validateUsageData(usageData: DailyContractUsageCacheableResponse) {
    const intersect = _.intersection(
      this.contracts.map((c) => c.name),
      usageData.monitoredContracts.map((c) => c.name),
    );

    if (intersect.length !== usageData.monitoredContracts.length) {
      throw new Error(
        "Missing some expected contracts in the database. No resolution at the moment",
      );
    }
  }

  protected async createEventsForDay(
    contractId: number,
    day: DailyContractUsageRow,
  ) {
    const userIds = day.userAddresses.map((addr) => {
      const id = this.userAddressToId(addr);
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

    // Create an event that reports the aggregate transaction information with
    // no contributor information
    tx.push(
      this.prisma.event.create({
        data: {
          eventTime: day.date,
          eventType: EventType.CONTRACT_INVOKED_AGGREGATE_STATS,
          artifactId: contractId,
          amount: 0,
          details: {
            totalL2GasCostGwei: day.contractTotalL2GasCostGwei,
            totalTxCount: day.contractTotalTxCount,
            uniqueSafeAddresses: day.uniqueSafeAddressCount,
          },
        },
      }),
    );

    await this.prisma.$transaction(tx);
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

      // We should generalize this for transactions generally. Especially
      // transactions that don't depend on each other like this one.
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
}

export async function importDailyContractUsage(
  args: ImportDailyContractUsage,
): Promise<void> {
  logger.info("importing contract usage");

  const client = new DuneClient(DUNE_API_KEY);
  const syncer = new DailyContractUsageSyncer(client, prismaClient, {
    cacheDirectory: args.cacheDir,
    baseDate: args.baseDate,
  });

  await syncer.run();
  logger.info("done");
}
