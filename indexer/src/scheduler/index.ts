import { BatchEventRecorder } from "../recorder/recorder.js";
import { BaseScheduler, Config, ExecutionMode } from "./types.js";
import {
  TimeSeriesCacheManager,
  TimeSeriesCacheWrapper,
} from "../cacher/time-series.js";
import { CommonArgs } from "../utils/api.js";
import { DateTime } from "luxon";
import { EventPointerManager } from "./pointers.js";
import { FundingEventsCollector } from "../collectors/dune-funding-events.js";
import { FundingEventsClient } from "../collectors/dune/funding-events/client.js";
import { DuneClient } from "@cowprotocol/ts-dune-client";
import {
  DUNE_API_KEY,
  DUNE_CSV_DIR_PATH,
  REDIS_URL,
  GITHUB_TOKEN,
  GITHUB_WORKERS_OWNER,
  GITHUB_WORKERS_REF,
  GITHUB_WORKERS_REPO,
  GITHUB_WORKERS_WORKFLOW_ID,
} from "../config.js";
import {
  ArtifactNamespace,
  ArtifactType,
  CollectionType,
  EventType,
  Recording,
} from "../db/orm-entities.js";
import { EventPointerRepository } from "../db/events.js";
import { ArtifactRepository } from "../db/artifacts.js";
import { AppDataSource } from "../db/data-source.js";
import { ProjectRepository } from "../db/project.js";
import { Octokit } from "octokit";
import { throttling } from "@octokit/plugin-throttling";
import { GithubCommitCollector } from "../collectors/github-commits.js";
import { GithubIssueCollector } from "../collectors/github-issues.js";
import { GithubFollowingCollector } from "../collectors/github-followers.js";
import { DailyContractUsageCollector } from "../collectors/dune-daily-contract-usage.js";
import { DailyContractUsageClient } from "../collectors/dune/daily-contract-usage/client.js";
import path from "path";
import { GithubWorkerSpawner } from "./github.js";
import { JobExecutionRepository, JobsRepository } from "../db/jobs.js";
import { NpmDownloadCollector } from "../collectors/npm-downloads.js";
import { DependentsPeriodicCollector } from "../collectors/dependents.js";
import { CollectionRepository } from "../db/collection.js";
import { BigQuery } from "@google-cloud/bigquery";
import { DuneCSVUploader } from "../collectors/dune/utils/csv-uploader.js";
import { createClient } from "redis";

export type SchedulerArgs = CommonArgs & {
  recorderTimeoutMs: number;
  overwriteExistingEvents: boolean;
  batchSize: number;
  recorderConnections: number;
};

export type SchedulerManualArgs = SchedulerArgs & {
  collector: string;
  startDate: DateTime;
  endDate: DateTime;
  executionMode: ExecutionMode;
  reindex: boolean;
};

export type SchedulerWorkerArgs = SchedulerArgs & {
  group: string;
  resumeWithLock: boolean;
};

export type SchedulerQueueAllArgs = SchedulerArgs & {
  baseDate: DateTime;
};

export type SchedulerQueueJobArgs = SchedulerArgs & {
  collector: string;
  baseDate: DateTime;
  startDate: DateTime;
  endDate: DateTime;
};

export type SchedulerQueueBackfill = SchedulerArgs & {
  collector: string;
  startDate: DateTime;
  endDate: DateTime;
  backfillIntervalDays: number;
};

// Entrypoint for the scheduler. Currently not where it should be but this is quick.
export async function configure(args: SchedulerArgs) {
  const cacheManager = new TimeSeriesCacheManager(args.cacheDir);
  const cache = new TimeSeriesCacheWrapper(cacheManager);

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
        } else {
          octokit.log.error("failed too many times waiting for github quota");
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

  const config = new Config();
  const eventPointerManager = new EventPointerManager(
    AppDataSource,
    EventPointerRepository,
    {
      batchSize: args.batchSize,
    },
  );

  const spawner = new GithubWorkerSpawner(gh, {
    owner: GITHUB_WORKERS_OWNER,
    repo: GITHUB_WORKERS_REPO,
    ref: GITHUB_WORKERS_REF,
    workflowId: GITHUB_WORKERS_WORKFLOW_ID,
  });

  const redisClient = createClient({
    url: REDIS_URL,
  });

  // Used to allow for lazy loading of the redis client. This is a hack to
  // disable redis when it's not needed for some scheduler commands
  const redisFactory = async () => {
    if (!redisClient.isReady) {
      await redisClient.connect();
    }
    return redisClient;
  };

  const scheduler = new BaseScheduler(
    args.runDir,
    () => {
      const recorder = new BatchEventRecorder(
        AppDataSource,
        [],
        AppDataSource.getRepository(Recording),
        AppDataSource.getRepository(EventType),
        redisFactory,
        {
          timeoutMs: args.recorderTimeoutMs,
        },
      );
      recorder.setOptions({
        overwriteExistingEvents: args.overwriteExistingEvents,
      });
      return Promise.resolve(recorder);
    },
    config,
    eventPointerManager,
    cache,
    spawner,
    JobsRepository,
    JobExecutionRepository,
  );
  const dune = new DuneClient(DUNE_API_KEY);

  scheduler.registerEventCollector({
    create: async (_config, recorder, cache) => {
      const client = new FundingEventsClient(dune);

      const collector = new FundingEventsCollector(
        client,
        ProjectRepository,
        recorder,
        cache,
        10000,
      );
      return collector;
    },
    name: "dune-funding-events",
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

  scheduler.registerEventCollector({
    create: async (_config, recorder, cache) => {
      const collector = new GithubCommitCollector(
        ProjectRepository,
        gh,
        recorder,
        cache,
        // Arrived at this batch size through trial and error. 500 was too much.
        // Many "Premature close" errors. The less we have the less opportunity
        // for HTTP5XX errors it seems. This batch size is fairly arbitrary.
        50,
      );
      return collector;
    },
    name: "github-commits",
    description: "Collects github commits",
    group: "github",
    schedule: "daily",
    dataSetIncludesNow: true,
    artifactScope: [ArtifactNamespace.GITHUB],
    artifactTypeScope: [
      ArtifactType.GITHUB_ORG,
      ArtifactType.GITHUB_USER,
      ArtifactType.GIT_EMAIL,
      ArtifactType.GIT_NAME,
      ArtifactType.GIT_REPOSITORY,
    ],
  });

  scheduler.registerEventCollector({
    create: async (_config, recorder, cache) => {
      const collector = new GithubIssueCollector(
        ProjectRepository,
        recorder,
        cache,
        100,
      );
      return collector;
    },
    name: "github-issues",
    description: "Collects github pull requests and issues",
    group: "github",
    schedule: "daily",
    dataSetIncludesNow: true,
    artifactScope: [ArtifactNamespace.GITHUB],
    artifactTypeScope: [
      ArtifactType.GITHUB_ORG,
      ArtifactType.GITHUB_USER,
      ArtifactType.GIT_EMAIL,
      ArtifactType.GIT_NAME,
      ArtifactType.GIT_REPOSITORY,
    ],
  });

  scheduler.registerEventCollector({
    create: async (_config, recorder, cache) => {
      const collector = new GithubFollowingCollector(
        ProjectRepository,
        recorder,
        cache,
        10,
      );
      return collector;
    },
    name: "github-followers",
    description: "Collects github pull requests and issues",
    group: "github",
    schedule: "daily",
    dataSetIncludesNow: true,
    artifactScope: [ArtifactNamespace.GITHUB],
    artifactTypeScope: [
      ArtifactType.GITHUB_ORG,
      ArtifactType.GITHUB_USER,
      ArtifactType.GIT_EMAIL,
      ArtifactType.GIT_NAME,
      ArtifactType.GIT_REPOSITORY,
    ],
  });

  scheduler.registerEventCollector({
    create: async (_config, recorder, cache) => {
      const client = new DailyContractUsageClient(
        dune,
        new DuneCSVUploader(DUNE_API_KEY),
        {
          csvDirPath: DUNE_CSV_DIR_PATH,
        },
      );
      const collector = new DailyContractUsageCollector(
        client,
        ProjectRepository,
        recorder,
        cache,
        {
          knownUserAddressesSeedPath: path.join(
            args.cacheDir,
            "known-user-addresses-seed.json",
          ),
          mode: "api",
        },
      );
      return collector;
    },
    name: "dune-daily-contract-usage",
    description: "Collects github pull requests and issues",
    group: "dune",
    schedule: "daily",
    artifactScope: [ArtifactNamespace.OPTIMISM],
    artifactTypeScope: [
      ArtifactType.CONTRACT_ADDRESS,
      ArtifactType.FACTORY_ADDRESS,
      ArtifactType.EOA_ADDRESS,
      ArtifactType.SAFE_ADDRESS,
    ],
  });

  scheduler.registerEventCollector({
    create: async (_config, recorder, cache) => {
      const collector = new NpmDownloadCollector(
        ProjectRepository,
        recorder,
        cache,
        200,
      );
      return collector;
    },
    name: "npm-downloads",
    description: "Collects npm download metrics by day",
    group: "npm",
    schedule: "daily",
    artifactScope: [ArtifactNamespace.NPM_REGISTRY],
    artifactTypeScope: [ArtifactType.NPM_PACKAGE],
  });

  scheduler.registerPeriodicCollector({
    create: async (_config, _cache) => {
      return new DependentsPeriodicCollector(
        ArtifactRepository,
        CollectionRepository,
        AppDataSource.getRepository(CollectionType),
        ProjectRepository,
        new BigQuery(),
        "opensource_observer",
      );
    },
    name: "dependents",
    description: "Periodically collect dependencies",
    schedule: "monthly",
  });

  return scheduler;
}
