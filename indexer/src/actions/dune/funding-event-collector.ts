import { DateTime } from "luxon";
import { logger } from "../../utils/logger.js";
import {
  FundingPoolAddress,
  IFundingEventsClient,
  ProjectAddress,
} from "./funding-events/client.js";
import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  EventType,
  Project,
} from "../../db/orm-entities.js";
import {
  IEventRecorder,
  IncompleteArtifact,
  IncompleteEvent,
} from "../../recorder/types.js";
import {
  TimeSeriesCacheLookup,
  TimeSeriesCacheWrapper,
} from "../../cacher/time-series.js";
import _ from "lodash";
import { IArtifactGroup, ICollector } from "../../scheduler/types.js";
import { Range } from "../../utils/ranges.js";
import { asyncBatch } from "../../utils/array.js";
import { ProjectRepository } from "../../db/project.js";
import { ProjectArtifactGroup } from "../../scheduler/common.js";

export interface FundingEventsCollectorOptions {
  cacheOptions: {
    bucket: string;
  };
}

export const DefaultFundingEventsCollectorOptions: FundingEventsCollectorOptions =
  {
    cacheOptions: {
      bucket: "funding-events",
    },
  };

export class FundingEventsCollector implements ICollector {
  private client: IFundingEventsClient;
  private recorder: IEventRecorder;
  private projectRepository: typeof ProjectRepository;
  private cache: TimeSeriesCacheWrapper;
  private options: FundingEventsCollectorOptions;

  constructor(
    client: IFundingEventsClient,
    projectRepository: typeof ProjectRepository,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    options?: Partial<FundingEventsCollectorOptions>,
  ) {
    this.client = client;
    this.projectRepository = projectRepository;
    this.recorder = recorder;
    this.options = _.merge(DefaultFundingEventsCollectorOptions, options);
    this.cache = cache;
  }

  async *groupedArtifacts(): AsyncGenerator<IArtifactGroup<Project>> {
    logger.debug("gathering artifacts");
    const projects =
      await this.projectRepository.allFundableProjectsWithAddresses();

    for (const project of projects) {
      const artifacts: Artifact[] = project.artifacts
        .filter((a) => a.name.length == 42)
        .map((a) => {
          return a;
        });
      yield ProjectArtifactGroup.create(project, artifacts);
    }
  }

  async collect(
    group: IArtifactGroup<Project>,
    range: Range,
    commitArtifact: (artifact: Artifact) => Promise<void>,
  ): Promise<void> {
    logger.debug("running funding events collector");
    const artifacts = await group.artifacts();
    // Super pragmatic hack for now to create the funding addresses. Let's just make them now
    const fundingAddressesRaw: Array<[string, string, string, string]> = [
      [
        "Optimism",
        "0x19793c7824be70ec58bb673ca42d2779d12581be",
        "RPGF2",
        "optimism",
      ],
      [
        "DAO Drops",
        "0xafe5f7a1d1c173b311047cdc93729013ad03de0c",
        "DAO Drops 1",
        "mainnet",
      ],
      [
        "Ethereum Foundation",
        "0x9ee457023bb3de16d51a003a247baead7fce313d",
        "Grants Provider",
        "mainnet",
      ],
      [
        "Gitcoin",
        "0x2878883dd4345c7b35c13fefc5096dd400814d91",
        "GR14",
        "mainnet",
      ],
      [
        "Gitcoin",
        "0xf63fd0739cb68651efbd06bccb23f1a1623d5520",
        "GR13",
        "mainnet",
      ],
      [
        "Gitcoin",
        "0xab8d71d59827dcc90fedc5ddb97f87effb1b1a5b",
        "GR12",
        "mainnet",
      ],
      [
        "Gitcoin",
        "0x0ebd2e2130b73107d0c45ff2e16c93e7e2e10e3a",
        "GR11",
        "mainnet",
      ],
      [
        "Gitcoin",
        "0x3ebaffe01513164e638480404c651e885cca0aa4",
        "GR10",
        "mainnet",
      ],
      [
        "Gitcoin",
        "0x3342e3737732d879743f2682a3953a730ae4f47c",
        "GR9",
        "mainnet",
      ],
      [
        "Gitcoin",
        "0xf2354570be2fb420832fb7ff6ff0ae0df80cf2c6",
        "GR8",
        "mainnet",
      ],
      [
        "Gitcoin",
        "0x7d655c57f71464b6f83811c55d84009cd9f5221c",
        "Bulk Checkout",
        "mainnet",
      ],
    ];

    const fundingAddressesAsContributors: IncompleteArtifact[] =
      fundingAddressesRaw.map((r) => {
        return {
          name: r[1],
          namespace:
            r[3] === "optimism"
              ? ArtifactNamespace.OPTIMISM
              : ArtifactNamespace.ETHEREUM,
          type: ArtifactType.CONTRACT_ADDRESS,
          details: {
            fundingPoolName: r[2],
            blockchain: r[3],
            contributorGroup: r[0],
          },
        };
      });

    const fundingAddressesInput: FundingPoolAddress[] = fundingAddressesRaw.map(
      (r, i) => {
        return {
          id: i,
          groupId: i,
          address: r[1],
        };
      },
    );

    const fundingAddressMap = fundingAddressesAsContributors.reduce<
      Record<string, IncompleteArtifact>
    >((acc, curr) => {
      acc[curr.name] = curr;
      return acc;
    }, {});

    const projectAddressesInput: Array<
      ProjectAddress & { namespace: ArtifactNamespace; type: ArtifactType }
    > = artifacts.map((a, i) => {
      return {
        id: i,
        projectId: i,
        address: a.name.toLowerCase(),
        namespace: a.namespace,
        type: a.type,
      };
    });
    const addressLookupMap = projectAddressesInput.reduce<
      Record<string, (typeof projectAddressesInput)[number]>
    >((a, c) => {
      a[c.address] = c;
      return a;
    }, {});

    const projectAddressesMap = projectAddressesInput.reduce<
      Record<string, IncompleteArtifact>
    >((acc, curr) => {
      acc[curr.address] = {
        name: curr.address,
        namespace: curr.namespace,
        type: curr.type,
      };
      return acc;
    }, {});

    // Create a lookup
    const responses = this.cache.loadCachedOrRetrieve(
      TimeSeriesCacheLookup.new(
        this.options.cacheOptions.bucket,
        projectAddressesInput.map((a) => a.address),
        range,
      ),
      async (missing) => {
        return this.client.getFundingEvents(
          missing.range.startDate,
          missing.range.endDate,
          fundingAddressesInput,
          missing.keys.map((a) => addressLookupMap[a]),
        );
      },
    );

    const recordPromises: Promise<string>[] = [];

    for await (const res of responses) {
      for (const row of res.raw) {
        const artifact = projectAddressesMap[row.to];
        if (!artifact) {
          logger.warn(`found an empty artifact for ${row.to}`);
          continue;
        }
        const contributor = fundingAddressMap[row.from];
        let amountAsFloat = 0.0;
        try {
          amountAsFloat = parseFloat(row.value);
        } catch (e) {
          logger.error(
            "failed to parse amount as a float. The value is still stored as a string",
          );
        }

        const event: IncompleteEvent = {
          time: DateTime.fromISO(row.blockTime, { zone: "utc" }),
          type: EventType.FUNDING,
          to: artifact,
          from: contributor,
          sourceId: row.txHash,

          // Worried this could fail on very large values
          amount: amountAsFloat,
          details: {
            amountAsString: row.value,
            txHash: row.txHash,
            token: row.token,
            blockchain: row.blockchain,
          },
        };

        recordPromises.push(this.recorder.record(event));
      }
    }

    await Promise.all(recordPromises);

    // Commit all of the artifacts
    await asyncBatch(artifacts, 1, async (a) => {
      return await commitArtifact(a[0]);
    });
  }
}
