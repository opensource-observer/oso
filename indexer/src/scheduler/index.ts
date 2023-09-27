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
import { DUNE_API_KEY } from "../config.js";
import { ArtifactNamespace, ArtifactType } from "../db/orm-entities.js";
import { EventPointerRepository, EventRepository } from "../db/events.js";
import { ArtifactRepository } from "../db/artifacts.js";
import { AppDataSource } from "../db/data-source.js";
import { ProjectRepository } from "../db/project.js";

export type SchedulerArgs = CommonArgs & {
  collector: string;
  skipExisting?: boolean;
  startDate: DateTime;
  endDate: DateTime;
  batchSize: number;
};

// Entrypoint for the scheduler. Currently not where it should be but this is quick.
export async function defaults(args: SchedulerArgs) {
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

  return await scheduler.executeForRange(args.collector, {
    startDate: args.startDate,
    endDate: args.endDate,
  });
}
