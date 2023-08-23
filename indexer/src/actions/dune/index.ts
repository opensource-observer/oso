import { DuneClient } from "@cowprotocol/ts-dune-client";
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
  Event,
  Prisma,
  PrismaPromise,
} from "@prisma/client";
import { DUNE_API_KEY } from "../../config.js";
import fsPromises from "fs/promises";
import path from "path";
import { prisma as prismaClient } from "../../db/prisma-client.js";
import {
  DailyContractUsageClient,
  IDailyContractUsageClient,
  DailyContractUsageRow,
  DailyContractUsageResponse,
  resolveDailyContractUsage,
} from "./daily-contract-usage/client.js";
import { streamFindAll as allEvents } from "../../db/events.js";
import { streamFindAll as allContributors } from "../../db/contributors.js";
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

  // User address create batch size
  batchCreateSize: number;

  // batch read size
  batchReadSize: number;
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

    batchCreateSize: 2500,

    batchReadSize: 10000,
  };

export class DailyContractUsageSyncer {
  private client: IDailyContractUsageClient;
  private prisma: PrismaClient;
  private options: DailyContractUsageSyncerOptions;
  private allUsers: Contributor[];
  private userAddressToIdMap: { [address: string]: number };
  private contractsAlreadySynced: { [address: string]: boolean };
  private contracts: Awaited<ReturnType<typeof getMonitoredContracts>>;
  private contractAddressToIdMap: { [address: string]: number };

  constructor(
    client: IDailyContractUsageClient,
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
    // Loads the system state into memory (this won't scale indefinitely but
    // likely for a while) so that we can quickly process information without
    // having to do too many db requests to do mapping. This is a tradeoff
    // between storing users and contract addresses in the database such that it
    // can stored more efficiently. For now this should be fine.

    // Load contracts we monitor
    await this.loadAllContracts();

    // Load all the users we have in the database
    await this.loadAllUsers();

    // Retrieve the data for a given interval (it might load from cache)
    logger.info("loading contract usage data");
    const usageData = await this.retrieveUsageData();

    // Attempting to retrieve usage data can shift the baseDate (if we detect a
    // cache from within the current interval). So we need to check for the
    // currently synced contracts based on that baseDate;
    await this.loadSyncedContracts();

    const uniqueUserAddresses = usageData.uniqueUserAddresses();
    await this.ensureUsersExist(uniqueUserAddresses);

    logger.info("Add all events by contract address");
    await usageData.mapRowsByContractAddress(async (contractAddress, days) => {
      const contractId = this.contractAddressToId(contractAddress);
      if (!contractId) {
        throw new Error(`no matching contract id found for ${contractAddress}`);
      }
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
    });
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
    this.allUsers = [];
    const allUserStream = allContributors(
      this.prisma,
      this.options.batchReadSize,
      { namespace: ContributorNamespace.EOA_ADDRESS },
    );

    for await (const user of allUserStream) {
      const contributor = user as Contributor;
      this.allUsers.push(contributor);
    }

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

  protected async retrieveUsageData(): Promise<DailyContractUsageResponse> {
    // Load all necessary sync related data
    let usageData = await this.retrieveFromCache();
    if (usageData) {
      logger.info("loaded data from cache");
      // FIXME: Right now the caching assumes that the contracts we're
      // monitoring does not change (ie... we're not going to index anything
      // more in the past). Once we do we should put the logic here to handle
      // that case. For now. do nothing :)
    } else {
      // Get most active users from the previous interval
      let knownUserAddresses = await getKnownUserAddressesWithinTimeFrame(
        this.prisma,
        this.startDate.minus(
          Duration.fromObject({ days: this.options.intervalLengthInDays }),
        ),
        this.endDate.minus(
          Duration.fromObject({ days: this.options.intervalLengthInDays }),
        ),
        MAX_KNOWN_ADDRESSES,
      );

      if (knownUserAddresses.length === 0) {
        knownUserAddresses = await this.loadKnownAddressesSeed();
      }

      usageData = await this.retrieveFromDune(knownUserAddresses);
    }
    // Validate the given data to process
    this.validateUsageData(usageData);

    return usageData;
  }

  protected async retrieveFromDune(
    knownUserAddresses: Awaited<
      ReturnType<typeof getKnownUserAddressesWithinTimeFrame>
    >,
  ): Promise<DailyContractUsageResponse> {
    const response = await this.client.getDailyContractUsage(
      this.startDate,
      this.endDate,
      knownUserAddresses.map((u) => u.name),
      // Just load all contracts for now
      this.contracts.map((c) => c.name),
    );

    // Write this to cache
    await fsPromises.writeFile(this.intervalCachePath(), response.toJSON(), {
      encoding: "utf-8",
    });

    return response;
  }

  protected async retrieveFromCache(): Promise<
    DailyContractUsageResponse | undefined
  > {
    // We should try not to duplicate date. This method will choose to use a
    // cache if it falls within the same interval.
    const cachePaths = this.possibleCachePathsWithinInterval();
    let cachePath = "";
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
    return await DailyContractUsageResponse.fromJSON(cachePath);
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

  protected validateUsageData(usageData: DailyContractUsageResponse) {
    const intersect = _.intersection(
      this.contracts.map((c) => c.name),
      usageData.contractAddresses,
    );

    if (intersect.length !== usageData.contractAddresses.length) {
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

    const existingEventsStream = allEvents(
      this.prisma,
      this.options.batchReadSize,
      {
        eventTime: day.date,
        eventType: EventType.CONTRACT_INVOKED,
        contributorId: {
          in: userIds,
        },
        artifactId: contractId,
      },
    );

    // Check which users already have data written for that day.
    // We'll need to update those
    const existingEvents: Event[] = [];
    const existingEventsMap: { [id: number]: Array<number> } = {};
    for await (const raw of existingEventsStream) {
      const event = raw as Event;
      existingEvents.push(event);
      if (!event.contributorId) {
        return;
      }
      const eventIds = existingEventsMap[event.contributorId] ?? [];
      eventIds.push(event.id);
      existingEventsMap[event.contributorId] = eventIds;
    }

    let txs: PrismaPromise<Event>[] = [];
    let progress = 0;

    logger.info(
      `creating ${
        userIds.length
      } events for contract Artifact<${contractId}> on ${day.date.toISOString()}...`,
      {
        contractId: contractId,
        date: day.date,
        userIdsLength: userIds.length,
      },
    );
    for (const id of userIds) {
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
        txs.push(
          this.prisma.event.update({
            where: {
              id: existingEvents[0],
            },
            data: data,
          }),
        );
      } else {
        txs.push(
          this.prisma.event.create({
            data: data,
          }),
        );
      }

      if (txs.length > this.options.batchCreateSize) {
        await this.prisma.$transaction(txs);
        progress += txs.length;
        logger.debug(`committed ${progress}/${userIds.length} events`, {
          contractId: contractId,
          date: day.date,
          userIdsLength: userIds.length,
        });
        txs = [];
      }
    }

    if (txs.length !== 0) {
      await this.prisma.$transaction(txs);
      progress += txs.length;
      logger.debug(`committed ${progress}/${userIds.length} events`, {
        contractId: contractId,
        date: day.date,
        userIdsLength: userIds.length,
      });
    }

    // Create an event that reports the aggregate transaction information with
    // no contributor information
    await this.prisma.event.create({
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
    });
  }

  protected async ensureUsersExist(addresses: string[]) {
    logger.info("Add any new users for this time period");

    // Load all the currently known users
    await this.loadAllUsers();

    const existingAddresses = this.allUsers.map((u) => {
      return u.name;
    });
    const addressesToAdd = _.difference(addresses, existingAddresses);

    logger.debug(
      `adding ${addressesToAdd.length} new EOA_ADDRESS contributors`,
      {
        addressesToAddCount: addressesToAdd.length,
      },
    );

    // Query for all users in the response data so we can insert any that do not
    // exist
    const batchSize = this.options.batchCreateSize;
    for (let i = 0; i < addressesToAdd.length; i += batchSize) {
      const addressSlice = addressesToAdd.slice(i, i + batchSize);
      await this.prisma.contributor.createMany({
        data: addressSlice.map((a) => {
          return {
            name: a,
            namespace: ContributorNamespace.EOA_ADDRESS,
          };
        }),
      });
      const completed = i + addressSlice.length;
      logger.debug(
        `wrote ${batchSize} EOA_ADDRESSES to contributors. Progress (${completed}/${addressesToAdd.length})`,
        {
          addressesToAddCount: addressesToAdd.length,
          completed: completed,
        },
      );
    }

    await this.loadAllUsers();
  }
}

export async function importDailyContractUsage(
  args: ImportDailyContractUsage,
): Promise<void> {
  logger.info("importing contract usage");

  const dune = new DuneClient(DUNE_API_KEY);
  const client = new DailyContractUsageClient(dune);
  const syncer = new DailyContractUsageSyncer(client, prismaClient, {
    cacheDirectory: args.cacheDir,
    baseDate: args.baseDate,
  });

  await syncer.run();
  logger.info("done");
}
