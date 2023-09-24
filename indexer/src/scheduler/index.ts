export {};
// import { BatchEventRecorder } from "../recorder/recorder.js";
// import { BaseScheduler, Config } from "./types.js";
// import { prisma as prismaClient } from "../db/prisma-client.js";
// import {
//   TimeSeriesCacheManager,
//   TimeSeriesCacheWrapper,
// } from "../cacher/time-series.js";
// import { CommonArgs } from "../utils/api.js";
// import { DateTime } from "luxon";
// import { EventPointerManager } from "./pointers.js";
// import { FundingEventsCollector } from "../actions/dune/funding-event-collector.js";
// import { FundingEventsClient } from "../actions/dune/funding-events/client.js";
// import { DuneClient } from "@cowprotocol/ts-dune-client";
// import { DUNE_API_KEY } from "../config.js";
// import { ArtifactNamespace, ContributorNamespace } from "@prisma/client";

// export type SchedulerArgs = CommonArgs & {
//   collector: string;
//   skipExisting?: boolean;
//   startDate: DateTime;
//   endDate: DateTime;
//   batchSize: number;
// };

// // Entrypoint for the scheduler. Currently not where it should be but this is quick.
// export async function defaults(args: SchedulerArgs) {
//   const recorder = new BatchEventRecorder(prismaClient);
//   const cacheManager = new TimeSeriesCacheManager(args.cacheDir);
//   const cache = new TimeSeriesCacheWrapper(cacheManager);
//   const config = new Config();
//   const eventPointerManager = new EventPointerManager(prismaClient, {
//     batchSize: args.batchSize,
//   });
//   const scheduler = new BaseScheduler(
//     recorder,
//     config,
//     eventPointerManager,
//     cache,
//   );

//   scheduler.registerCollector({
//     create: async (_config, recorder, cache) => {
//       const dune = new DuneClient(DUNE_API_KEY);
//       const client = new FundingEventsClient(dune);

//       const collector = new FundingEventsCollector(
//         client,
//         prismaClient,
//         recorder,
//         cache,
//       );
//       return collector;
//     },
//     name: "funding-events",
//     description: "gathers funding events",
//     group: "dune",
//     schedule: "weekly",
//     artifactScope: [ArtifactNamespace.OPTIMISM, ArtifactNamespace.ETHEREUM],
//     contributorScope: [
//       ContributorNamespace.EOA_ADDRESS,
//       ContributorNamespace.SAFE_ADDRESS,
//       ContributorNamespace.CONTRACT_ADDRESS,
//     ],
//   });

//   return await scheduler.executeForRange(args.collector, {
//     startDate: args.startDate,
//     endDate: args.endDate,
//   });
// }
