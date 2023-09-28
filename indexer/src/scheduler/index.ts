import { BatchEventRecorder } from "../recorder/recorder.js";
import { BaseScheduler, Config } from "./types.js";
import {
  TimeSeriesCacheManager,
  TimeSeriesCacheWrapper,
} from "../cacher/time-series.js";
import { CommonArgs } from "../utils/api.js";
import { DateTime } from "luxon";
import { EventPointerManager } from "./pointers.js";
import { FundingEventsCollector } from "../actions/dune/funding-event-collector.js";
import { FundingEventsClient } from "../actions/dune/funding-events/client.js";
import { DuneClient } from "@cowprotocol/ts-dune-client";
import { DUNE_API_KEY, GITHUB_TOKEN } from "../config.js";
import { ArtifactNamespace, ArtifactType } from "../db/orm-entities.js";
import { EventPointerRepository, EventRepository } from "../db/events.js";
import { ArtifactRepository } from "../db/artifacts.js";
import { AppDataSource } from "../db/data-source.js";
import { ProjectRepository } from "../db/project.js";
import { Octokit } from "octokit";
import { throttling } from "@octokit/plugin-throttling";
import { GithubCommitCollector } from "../actions/github/fetch/commits.js";
import { GithubIssueCollector } from "../actions/github/fetch/pull-requests.js";

export type SchedulerArgs = CommonArgs & {
  collector: string;
  skipExisting?: boolean;
  startDate: DateTime;
  endDate: DateTime;
  batchSize: number;
};

// Entrypoint for the scheduler. Currently not where it should be but this is quick.
export async function configure(args: SchedulerArgs) {
  const recorder = new BatchEventRecorder(EventRepository, ArtifactRepository);
  const cacheManager = new TimeSeriesCacheManager(args.cacheDir);
  const cache = new TimeSeriesCacheWrapper(cacheManager);
  const config = new Config();
  const eventPointerManager = new EventPointerManager(
    AppDataSource,
    EventPointerRepository,
    {
      batchSize: args.batchSize,
    },
  );
  const scheduler = new BaseScheduler(
    recorder,
    config,
    eventPointerManager,
    cache,
  );

  const AppOctoKit = Octokit.plugin(throttling);
  const gh = new AppOctoKit({
    auth: GITHUB_TOKEN,
    throttle: {
      onRateLimit: (retryAfter, options, octokit, retryCount) => {
        const opts = options as {
          method: string;
          url: string;
        };
        octokit.log.warn(
          `Request quota exhausted for request ${opts.method} ${opts.url}`,
        );
        // Retry up to 50 times (that should hopefully be more than enough)
        if (retryCount < 50) {
          octokit.log.info(`Retrying after ${retryAfter} seconds!`);
          return true;
        }
      },
      onSecondaryRateLimit: (retryAfter, options, octokit, retryCount) => {
        const opts = options as {
          method: string;
          url: string;
        };
        octokit.log.warn(
          `Secondary rate limit detected for ${opts.method} ${opts.url}`,
        );
        if (retryCount < 3) {
          octokit.log.info(`Retrying after ${retryAfter} seconds!`);
          return true;
        } else {
          octokit.log.info(`Failing now`);
        }
      },
    },
  });

  scheduler.registerCollector({
    create: async (_config, recorder, cache) => {
      const dune = new DuneClient(DUNE_API_KEY);
      const client = new FundingEventsClient(dune);

      const collector = new FundingEventsCollector(
        client,
        ProjectRepository,
        recorder,
        cache,
      );
      return collector;
    },
    name: "funding-events",
    description: "gathers funding events",
    group: "dune",
    schedule: "weekly",
    artifactScope: [ArtifactNamespace.OPTIMISM, ArtifactNamespace.ETHEREUM],
    artifactTypeScope: [
      ArtifactType.EOA_ADDRESS,
      ArtifactType.SAFE_ADDRESS,
      ArtifactType.CONTRACT_ADDRESS,
    ],
  });

  scheduler.registerCollector({
    create: async (_config, recorder, cache) => {
      const collector = new GithubCommitCollector(
        ProjectRepository,
        gh,
        recorder,
        cache,
      );
      return collector;
    },
    name: "github-commits",
    description: "Collects github commits",
    group: "github",
    schedule: "daily",
    artifactScope: [ArtifactNamespace.GITHUB],
    artifactTypeScope: [
      ArtifactType.GITHUB_USER,
      ArtifactType.GIT_EMAIL,
      ArtifactType.GIT_NAME,
      ArtifactType.GIT_REPOSITORY,
    ],
  });

  scheduler.registerCollector({
    create: async (_config, recorder, cache) => {
      const collector = new GithubIssueCollector(
        ProjectRepository,
        recorder,
        cache,
      );
      return collector;
    },
    name: "github-issues",
    description: "Collects github pull requests and issues",
    group: "github",
    schedule: "daily",
    artifactScope: [ArtifactNamespace.GITHUB],
    artifactTypeScope: [
      ArtifactType.GITHUB_USER,
      ArtifactType.GIT_EMAIL,
      ArtifactType.GIT_NAME,
      ArtifactType.GIT_REPOSITORY,
    ],
  });

  return await scheduler.executeForRange(args.collector, {
    startDate: args.startDate,
    endDate: args.endDate,
  });
}
