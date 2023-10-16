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
  IDailyContractUsageClientV2,
  DailyContractUsageRow,
} from "./daily-contract-usage/client.js";
import {
  IArtifactGroup,
  IArtifactGroupCommitmentProducer,
} from "../../scheduler/types.js";
import _ from "lodash";
import { Range } from "../../utils/ranges.js";
import {
  IEventRecorder,
  IncompleteArtifact,
  IncompleteEvent,
  RecordHandle,
} from "../../recorder/types.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../../cacher/time-series.js";
import { ArtifactRepository } from "../../db/artifacts.js";
import { generateSourceIdFromArray } from "../../utils/source-ids.js";
import { BaseCollector, BasicArtifactGroup } from "../../scheduler/common.js";
import { UniqueArray } from "../../utils/array.js";
import { ProjectRepository } from "../../db/project.js";
import { In } from "typeorm";

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

  mode: "csv" | "api";

  // This is the sha1 of the table used to store the monitored contractIds
  contractSha1: string;
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

    mode: "api",

    contractSha1: "da1aae77b853fc7c74038ee08eec441b10b89570",
  };

export class DailyContractUsageCollector extends BaseCollector<object> {
  private client: IDailyContractUsageClientV2;
  private artifactRepository: typeof ArtifactRepository;
  private recorder: IEventRecorder;
  private cache: TimeSeriesCacheWrapper;
  private options: DailyContractUsageSyncerOptions;
  private rowsProcessed: number;

  constructor(
    client: IDailyContractUsageClientV2,
    artifactRepository: typeof ArtifactRepository,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options: Partial<DailyContractUsageSyncerOptions> = DefaultDailyContractUsageSyncerOptions,
  ) {
    super();
    this.client = client;
    this.artifactRepository = artifactRepository;
    this.options = _.merge(DefaultDailyContractUsageSyncerOptions, options);
    this.recorder = recorder;
    this.cache = cache;
    this.rowsProcessed = 0;
  }

  async allArtifacts(): Promise<Artifact[]> {
    const artifacts: Artifact[] = [];
    for await (const group of this.groupedArtifacts()) {
      artifacts.push(...(await group.artifacts()));
    }
    return artifacts;
  }

  async *groupedArtifacts(): AsyncGenerator<IArtifactGroup<object>> {
    // Get all contracts
    const projects = await ProjectRepository.find({
      relations: {
        artifacts: true,
      },
      where: {
        artifacts: {
          type: In([ArtifactType.CONTRACT_ADDRESS]),
          namespace: ArtifactNamespace.OPTIMISM,
        },
      },
    });
    const allArtifacts = projects.flatMap((p) => p.artifacts);

    const uniqueArtifacts = new UniqueArray((a: Artifact) => a.id);
    allArtifacts.forEach((a) => uniqueArtifacts.push(a));
    yield new BasicArtifactGroup("ALL_CONTRACTS", {}, uniqueArtifacts.items());
  }

  async collect(
    group: IArtifactGroup,
    range: Range,
    committer: IArtifactGroupCommitmentProducer,
  ): Promise<void> {
    logger.info("loading contract usage data");
    const artifacts = await group.artifacts();
    //const contractAddresses = artifacts.map((a) => a.name);
    const contractsByAddressMap = _.keyBy(artifacts, "name");

    // There seems to be some duplicates. Let's keep track for logging for now.
    const uniqueEvents = new UniqueArray<string>((s) => s);

    try {
      if (this.options.mode === "api") {
        await this.collectFromApi(range, contractsByAddressMap, uniqueEvents);
      } else {
        await this.collectFromCsv(range, contractsByAddressMap, uniqueEvents);
      }
    } catch (err) {
      logger.error("error collecting contract usage");
    }

    console.log("done processing");
    for (const artifact of artifacts) {
      committer.commit(artifact).withResults({
        success: [],
        errors: [],
      });
    }
  }

  protected async collectFromApi(
    range: Range,
    contractsByAddressMap: _.Dictionary<Artifact>,
    uniqueEvents: UniqueArray<string>,
  ) {
    const responses = this.cache.loadCachedOrRetrieve(
      TimeSeriesCacheLookup.new(
        this.options.cacheOptions.bucket,
        this.options.contractSha1,
        range,
      ),
      async (missing) => {
        const rows = await this.client.getDailyContractUsage(
          missing.range,
          this.options.contractSha1,
        );
        return {
          raw: rows,
          hasNextPage: false,
          cacheRange: missing.range,
        };
      },
    );

    for await (const page of responses) {
      const recordHandles: RecordHandle[] = [];
      for (const row of page.raw) {
        const contract = contractsByAddressMap[row.contractAddress];
        const event = await this.createEvents(contract, row, uniqueEvents);
        recordHandles.push(event);
      }
      await this.recorder.wait(recordHandles);
    }
  }

  protected async collectFromCsv(
    range: Range,
    contractsByAddressMap: _.Dictionary<Artifact>,
    uniqueEvents: UniqueArray<string>,
  ) {
    let currentTime = range.startDate;
    while (currentTime < range.endDate) {
      logger.debug(`loading ${currentTime.toISODate()}`);
      const rows = await this.client.getDailyContractUsageFromCsv(
        currentTime,
        this.options.contractSha1,
      );
      const recordHandles: RecordHandle[] = [];

      currentTime = currentTime.plus({ day: 1 });
      for (const row of rows) {
        const contract = contractsByAddressMap[row.contractAddress];
        const event = await this.createEvents(contract, row, uniqueEvents);
        recordHandles.push(event);
      }
      await this.recorder.wait(recordHandles);
    }
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

  // protected retrieveFromDune(
  //   range: Range,
  // ) {
  //   logger.debug("retrieving data from dune");
  //   const response = this.client.getDailyContractUsage(
  //     range.startDate,
  //     range.endDate,
  //     "da1aae77b853fc7c74038ee08eec441b10b89570"
  //   );

  //   return response;
  // }

  protected async createEvents(
    contract: Artifact,
    row: DailyContractUsageRow,
    uniqueTracker: UniqueArray<string>,
  ): Promise<RecordHandle> {
    this.rowsProcessed += 1;
    const eventTime = DateTime.fromISO(row.date);

    if (!row.userAddress && !row.safeAddress) {
      throw new Error("unexpectd no address");
    }

    const from: IncompleteArtifact =
      row.safeAddress === null
        ? {
            name: row.userAddress!,
            type: ArtifactType.EOA_ADDRESS,
            namespace: ArtifactNamespace.OPTIMISM,
          }
        : {
            name: row.safeAddress,
            type: ArtifactType.SAFE_ADDRESS,
            namespace: ArtifactNamespace.OPTIMISM,
          };

    const recorderContract =
      contract !== undefined
        ? contract
        : {
            name: row.contractAddress,
            type: ArtifactType.CONTRACT_ADDRESS,
            namespace: ArtifactNamespace.OPTIMISM,
          };

    const sourceId = generateSourceIdFromArray([
      EventType.CONTRACT_INVOKED,
      eventTime.toISODate()!,
      recorderContract.name,
      recorderContract.namespace,
      recorderContract.type,
      from.name,
      from.namespace,
      from.type,
    ]);

    // Convert gasCost to a bigint
    let gasCost = BigInt(0);
    try {
      gasCost = BigInt(row.gasCostGwei);
    } catch (err) {
      console.warn(
        `Could not get gasCost for ${sourceId}. Value ${row.gasCostGwei} is not a number`,
      );
    }

    // Check which users already have data written for that day.
    // We'll need to update those
    const event: IncompleteEvent = {
      time: eventTime,
      type: EventType.CONTRACT_INVOKED,
      to: recorderContract,
      from: from,
      amount: row.txCount,
      size: gasCost,
      sourceId: sourceId,
    };

    const beforeAddLen = uniqueTracker.length;
    uniqueTracker.push(event.sourceId);
    if (uniqueTracker.length === beforeAddLen) {
      console.log("Duplicates");
      console.log(`SourceId=${event.sourceId}`);
    }

    return await this.recorder.record(event);
  }
}
