import { DateTime } from "luxon";
import { CommonArgs } from "../../utils/api.js";
import { logger } from "../../utils/logger.js";
import {
  EventType,
  Artifact,
  ArtifactNamespace,
  ArtifactType,
} from "../../db/orm-entities.js";
import fsPromises from "fs/promises";
import {
  IDailyContractUsageClient,
  DailyContractUsageRow,
  DailyContractUsageResponse,
} from "./daily-contract-usage/client.js";
import { ArtifactGroup, ICollector } from "../../scheduler/types.js";
import _ from "lodash";
import { Range } from "../../utils/ranges.js";
import {
  IEventRecorder,
  IncompleteArtifact,
  IncompleteEvent,
} from "../../recorder/types.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../../cacher/time-series.js";
import { ArtifactRepository } from "../../db/artifacts.js";
import { generateSourceIdFromArray } from "../../utils/source-ids.js";

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

  knownUserAddressesSeedPath: string;

  // A cache directory for responses which will be used by github actions to
  // load any response we get from a previous run (tbd). This will hopefully
  // reduce our API credit usage within dune
  cacheOptions: {
    bucket: string;
  };

  // The query id in dune to call. The default is below
  contractUsersQueryId: number;

  // User address create batch size
  batchCreateSize: number;

  // batch read size
  batchReadSize: number;

  // Janky... currently passed into the DailyContractUsageResponse object to
  // dictate how many contracts we process in "parallel". This would essentially
  // dictate how many postgres connections we made (in theory?)
  parallelism: number;

  blockchain: ArtifactNamespace;
}

export const DefaultDailyContractUsageSyncerOptions: DailyContractUsageSyncerOptions =
  {
    intervalLengthInDays: 7,
    offsetDays: 2,
    cacheOptions: {
      bucket: "contract-daily-usage",
    },

    knownUserAddressesSeedPath: "/tmp/known-addresses-seed.json",

    // This default is based on this: https://dune.com/queries/2835126
    contractUsersQueryId: 2835126,

    batchCreateSize: 2500,

    batchReadSize: 10000,

    parallelism: 10,

    blockchain: ArtifactNamespace.OPTIMISM,
  };

export class DailyContractUsageCollector implements ICollector {
  private client: IDailyContractUsageClient;
  private artifactRepository: typeof ArtifactRepository;
  private recorder: IEventRecorder;
  private cache: TimeSeriesCacheWrapper;
  private options: DailyContractUsageSyncerOptions;

  constructor(
    client: IDailyContractUsageClient,
    artifactRepository: typeof ArtifactRepository,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options: Partial<DailyContractUsageSyncerOptions> = DefaultDailyContractUsageSyncerOptions,
  ) {
    this.client = client;
    this.artifactRepository = artifactRepository;
    this.options = _.merge(DefaultDailyContractUsageSyncerOptions, options);
    this.recorder = recorder;
    this.cache = cache;
  }

  async *groupedArtifacts(): AsyncGenerator<ArtifactGroup> {
    // Get all contracts
    const artifacts = await this.artifactRepository.find({
      where: {
        type: ArtifactType.CONTRACT_ADDRESS,
      },
    });
    yield {
      artifacts: artifacts,
      details: {},
    };
  }

  private async loadKnownUserAddresses(range: Range): Promise<string[]> {
    logger.debug("loading known user addresses as input for dune");
    const largerRange: Range = {
      startDate: range.startDate.minus({ months: 1 }),
      endDate: DateTime.now(),
    };
    const frequentContributors =
      await this.artifactRepository.mostFrequentContributors(largerRange, [
        EventType.CONTRACT_INVOKED,
      ]);
    if (frequentContributors.length > 0) {
      return frequentContributors.map((c) => c.contributorName);
    }
    const seed = await this.loadKnownUserAddressesSeed();
    return seed.map((a) => a.name);
  }

  async collect(
    group: ArtifactGroup,
    range: Range,
    commitArtifact: (artifact: Artifact) => Promise<void>,
  ): Promise<void> {
    logger.info("loading contract usage data");
    const knownUserAddresses = await this.loadKnownUserAddresses(range);
    const contractAddresses = group.artifacts.map((a) => a.name);
    const contractsByAddressMap = _.keyBy(group.artifacts, "name");
    const responses = this.cache.loadCachedOrRetrieve<DailyContractUsageRow[]>(
      TimeSeriesCacheLookup.new(
        this.options.cacheOptions.bucket,
        contractAddresses,
        range,
      ),
      async (missing) => {
        const rows = await this.retrieveFromDune(
          range,
          group.artifacts,
          knownUserAddresses,
        );
        return {
          raw: rows,
          cacheRange: missing.range,
          hasNextPage: false,
        };
      },
    );

    for await (const page of responses) {
      const usageData = new DailyContractUsageResponse(
        page.raw,
        contractAddresses,
      );
      const contractPromises = usageData.mapRowsByContractAddress(
        async (address, rows) => {
          const contract = contractsByAddressMap[address];
          logger.debug(`events for ${contract.name}`);

          const eventPromises = rows.flatMap((row) => {
            return this.createEventsForDay(contract, row);
          });
          await Promise.all(eventPromises);
          logger.debug(`events for ${contract.name} recorded`);

          await commitArtifact(contract);
        },
      );

      logger.debug(
        `wait for all of the promises to resolve for contracts count ${contractPromises.length}`,
      );
      await Promise.all(contractPromises);
    }
    logger.debug("finished collection");
  }

  protected async loadKnownUserAddressesSeed(): Promise<
    { id: number; name: string }[]
  > {
    const knownAddressesSeedPath = this.options.knownUserAddressesSeedPath;

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

  protected async retrieveFromDune(
    range: Range,
    contracts: Artifact[],
    knownUserAddresses: string[],
  ): Promise<DailyContractUsageRow[]> {
    logger.debug("retrieving data from dune");
    const response = await this.client.getDailyContractUsage(
      range.startDate,
      range.endDate,
      knownUserAddresses,
      // Just load all contracts for now
      contracts.map((c) => c.name),
    );

    return response;
  }

  protected validateUsageData(
    contracts: Artifact[],
    usageData: DailyContractUsageResponse,
  ) {
    const intersect = _.intersection(
      contracts.map((c) => c.name),
      usageData.contractAddresses,
    );

    if (intersect.length !== usageData.contractAddresses.length) {
      throw new Error(
        "Missing some expected contracts in the database. No resolution at the moment",
      );
    }
  }

  protected createEventsForDay(contract: Artifact, day: DailyContractUsageRow) {
    const eventPromises: Promise<void>[] = [];
    const userArtifacts: IncompleteArtifact[] = day.userAddresses.map(
      (addr) => {
        return {
          name: addr,
          namespace: this.options.blockchain,
          type: ArtifactType.EOA_ADDRESS,
        };
      },
    );
    const eventTime = DateTime.fromISO(day.date).toUTC();

    // Check which users already have data written for that day.
    // We'll need to update those
    logger.info(
      `creating ${userArtifacts.length} events for contract Artifact<${
        contract.id
      }> on ${eventTime.toISO()}...`,
      {
        contractId: contract.id,
        date: day.date,
        userArtifactsLength: userArtifacts.length,
      },
    );
    for (const user of userArtifacts) {
      const event: IncompleteEvent = {
        time: eventTime,
        type: EventType.CONTRACT_INVOKED,
        to: contract,
        from: user,
        amount: 0,
        sourceId: generateSourceIdFromArray([
          EventType.CONTRACT_INVOKED,
          eventTime.toISODate()!,
          contract.name,
          contract.namespace,
          user.name,
          user.namespace,
        ]),
      };

      eventPromises.push(this.recorder.record(event));
    }

    // Create an event that reports the aggregate transaction information with
    // no contributor information
    eventPromises.push(
      this.recorder.record({
        time: eventTime,
        type: EventType.CONTRACT_INVOKED_AGGREGATE_STATS,
        to: contract,
        amount: 0,
        sourceId: generateSourceIdFromArray([
          EventType.CONTRACT_INVOKED_AGGREGATE_STATS,
          eventTime.toISODate()!,
          contract.name,
          contract.namespace,
        ]),
        details: {
          totalL2GasCostGwei: day.contractTotalL2GasCostGwei,
          totalTxCount: day.contractTotalTxCount,
          uniqueSafeAddresses: day.uniqueSafeAddressCount,
        },
      }),
    );
    return eventPromises;
  }
}

// export async function importDailyContractUsage(
//   args: ImportDailyContractUsage,
// ): Promise<void> {
//   logger.info("importing contract usage");

//   const dune = new DuneClient(DUNE_API_KEY);
//   const client = new DailyContractUsageClient(dune);
//   const syncer = new DailyContractUsageCollector(client, prismaClient, {
//     cacheDirectory: args.cacheDir,
//     baseDate: args.baseDate,
//   });

//   await syncer.run();
//   logger.info("done");
// }
