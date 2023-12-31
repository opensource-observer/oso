import { DateTime } from "luxon";
import { CommonArgs } from "../utils/api.js";
import { logger } from "../utils/logger.js";
import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
} from "../db/orm-entities.js";
import fsPromises from "fs/promises";
import {
  IDailyContractUsageClientV2,
  DailyContractUsageRow,
  Contract,
} from "./dune/daily-contract-usage/client.js";
import {
  IArtifactGroup,
  IArtifactGroupCommitmentProducer,
} from "../scheduler/types.js";
import _ from "lodash";
import { Range } from "../utils/ranges.js";
import {
  IEventRecorderClient,
  IncompleteArtifact,
  IncompleteEvent,
} from "../recorder/types.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../cacher/time-series.js";
import { sha1FromArray } from "../utils/source-ids.js";
import { BaseEventCollector, BasicArtifactGroup } from "../scheduler/common.js";
import { UniqueArray } from "../utils/array.js";
import { ProjectRepository } from "../db/project.js";
import { In } from "typeorm";
import { ArtifactGroupRecorder } from "../recorder/group.js";

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
  };

export class DailyContractUsageCollector extends BaseEventCollector<object> {
  private client: IDailyContractUsageClientV2;
  private projectRepository: typeof ProjectRepository;
  private recorder: IEventRecorderClient;
  private cache: TimeSeriesCacheWrapper;
  private options: DailyContractUsageSyncerOptions;
  private rowsProcessed: number;

  constructor(
    client: IDailyContractUsageClientV2,
    projectRepository: typeof ProjectRepository,
    recorder: IEventRecorderClient,
    cache: TimeSeriesCacheWrapper,
    options: Partial<DailyContractUsageSyncerOptions> = DefaultDailyContractUsageSyncerOptions,
  ) {
    super();
    this.client = client;
    this.projectRepository = projectRepository;
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
    const projects = await this.projectRepository.find({
      relations: {
        artifacts: true,
      },
      where: {
        artifacts: {
          type: In([
            ArtifactType.CONTRACT_ADDRESS,
            ArtifactType.FACTORY_ADDRESS,
          ]),
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
    const contractsByAddressMap = _.keyBy(artifacts, "name");

    // There seems to be some duplicates. Let's keep track for logging for now.
    const uniqueEvents = new UniqueArray<string>((s) => s);

    const groupRecorder = new ArtifactGroupRecorder(this.recorder);
    try {
      if (this.options.mode === "api") {
        await this.collectFromApi(
          groupRecorder,
          artifacts,
          range,
          contractsByAddressMap,
          uniqueEvents,
        );
      } else {
        await this.collectFromCsv(
          groupRecorder,
          range,
          contractsByAddressMap,
          uniqueEvents,
        );
      }
    } catch (err) {
      logger.error("error collecting contract usage");
      logger.error(err);
      throw err;
    }

    logger.debug("done processing contract calls");
    committer.commitGroup(groupRecorder);
  }

  protected async collectFromApi(
    groupRecorder: ArtifactGroupRecorder,
    artifacts: Artifact[],
    range: Range,
    contractsByAddressMap: _.Dictionary<Artifact>,
    uniqueEvents: UniqueArray<string>,
  ) {
    const contracts: Contract[] = artifacts.map((a) => {
      return {
        id: a.id,
        address: a.name.toLowerCase(),
      };
    });

    const responses = this.cache.loadCachedOrRetrieve(
      TimeSeriesCacheLookup.new(
        this.options.cacheOptions.bucket,
        contracts.map((c) => c.address),
        range,
      ),
      async (missing) => {
        const rows = await this.client.getDailyContractUsage(missing.range, {
          contracts: contracts,
        });
        return {
          raw: rows,
          hasNextPage: false,
          cacheRange: missing.range,
        };
      },
    );

    for await (const page of responses) {
      for (const row of page.raw) {
        const contract = contractsByAddressMap[row.contractAddress];
        await this.createEvents(groupRecorder, contract, row, uniqueEvents);
      }
    }
  }

  protected async collectFromCsv(
    groupRecorder: ArtifactGroupRecorder,
    range: Range,
    contractsByAddressMap: _.Dictionary<Artifact>,
    uniqueEvents: UniqueArray<string>,
  ) {
    let currentTime = range.startDate;
    while (currentTime < range.endDate) {
      logger.debug(`loading ${currentTime.toISODate()}`);
      const rows = await this.client.getDailyContractUsageFromCsv(currentTime);

      currentTime = currentTime.plus({ day: 1 });
      for (const row of rows) {
        const contract = contractsByAddressMap[row.contractAddress];
        await this.createEvents(groupRecorder, contract, row, uniqueEvents);
      }
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
    groupRecorder: ArtifactGroupRecorder,
    contract: Artifact,
    row: DailyContractUsageRow,
    uniqueTracker: UniqueArray<string>,
  ): Promise<void> {
    this.rowsProcessed += 1;
    const eventTime = DateTime.fromISO(row.date);

    if (!row.userAddress && !row.safeAddress) {
      throw new Error("unexpected: no address");
    }

    const from: IncompleteArtifact = !row.safeAddress
      ? {
          name: row.userAddress!.toLowerCase(),
          type: ArtifactType.EOA_ADDRESS,
          namespace: ArtifactNamespace.OPTIMISM,
          url: `https://optimistic.etherscan.io/address/${row.userAddress}`,
        }
      : {
          name: row.safeAddress.toLowerCase(),
          type: ArtifactType.SAFE_ADDRESS,
          namespace: ArtifactNamespace.OPTIMISM,
          url: `https://optimistic.etherscan.io/address/${row.safeAddress}`,
        };

    if (!row.contractAddress) {
      console.log(row);
      throw new Error("no artifact to record to");
    }
    const recorderContract =
      contract !== undefined
        ? contract
        : {
            name: row.contractAddress,
            type: ArtifactType.CONTRACT_ADDRESS,
            namespace: ArtifactNamespace.OPTIMISM,
            url: `https://optimistic.etherscan.io/address/${row.contractAddress}`,
          };

    const eventTimeAsStr = eventTime.toISODate();
    if (eventTimeAsStr === null) {
      throw new Error("event time must be a date");
    }

    const sourceId = sha1FromArray([
      "CONTRACT_INVOCATION",
      eventTimeAsStr,
      recorderContract.name,
      recorderContract.namespace,
      recorderContract.type,
      from.name,
      from.namespace,
      from.type,
    ]);

    // Convert gasCost to a bigint
    let l2GasAsFloat = 0;
    try {
      l2GasAsFloat = parseFloat(row.l2GasUsed);
    } catch (err) {
      console.warn(
        `Could not get gasCost for ${sourceId}. Value ${row.l2GasUsed} is not a number`,
      );
    }

    let l1GasAsFloat = 0;
    try {
      l1GasAsFloat = parseFloat(row.l1GasUsed);
    } catch (err) {
      console.warn(
        `Could not get gasCost for ${sourceId}. Value ${row.l1GasUsed} is not a number`,
      );
    }

    // Check which users already have data written for that day.
    // We'll need to update those
    const countEvent: IncompleteEvent = {
      time: eventTime,
      type: {
        name: "CONTRACT_INVOCATION_DAILY_COUNT",
        version: 1,
      },
      to: recorderContract,
      from: from,
      amount: row.txCount,
      sourceId: sourceId,
    };

    const l2GasUsedEvent: IncompleteEvent = {
      time: eventTime,
      type: {
        name: "CONTRACT_INVOCATION_DAILY_L2_GAS_USED",
        version: 1,
      },
      to: recorderContract,
      from: from,
      amount: l2GasAsFloat,
      sourceId: sourceId,
    };

    const l1GasUsedEvent: IncompleteEvent = {
      time: eventTime,
      type: {
        name: "CONTRACT_INVOCATION_DAILY_L1_GAS_USED",
        version: 1,
      },
      to: recorderContract,
      from: from,
      amount: l1GasAsFloat,
      sourceId: sourceId,
    };

    const beforeAddLen = uniqueTracker.length;
    uniqueTracker.push(countEvent.sourceId);
    if (uniqueTracker.length === beforeAddLen) {
      logger.debug(
        `duplicates for sourceId=${countEvent.sourceId} found for contract[${
          countEvent.to.name
        }] from address[${countEvent.from
          ?.name}] on ${countEvent.time.toISODate()}`,
      );
    }
    await groupRecorder.record(countEvent);
    await groupRecorder.record(l2GasUsedEvent);
    await groupRecorder.record(l1GasUsedEvent);
  }
}
