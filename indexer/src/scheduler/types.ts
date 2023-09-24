export {};
// import {
//   Artifact,
//   ArtifactNamespace,
//   ContributorNamespace,
//   EventType,
// } from "@prisma/client";
// import { IEventRecorder, IEventTypeStrategy } from "../recorder/types.js";
// import { Range, findMissingRanges, rangeFromDates } from "../utils/ranges.js";
// import { EventPointerManager } from "./pointers.js";
// import { TimeSeriesCacheWrapper } from "../cacher/time-series.js";

// export type ArtifactGroup = {
//   details: unknown;
//   artifacts: Artifact[];
// };

// /**
//  * The interface for the scheduler that manages all of the schedules for jobs
//  */
// export interface ICollector {
//   // Yield arrays of artifacts that this collector monitors. This is an async
//   // generator so that artifacts can be yielded in groups if needed.
//   groupedArtifacts(): AsyncGenerator<ArtifactGroup>;

//   collect(
//     group: ArtifactGroup,
//     range: Range,
//     commitArtifact: (artifact: Artifact) => Promise<void>,
//   ): Promise<void>;
// }

// /**
//  * Rudimentary service locator that uses names to register services. This isn't
//  * ideal but will work for now to ensure we can do dependency injection.
//  */
// export interface IConfig {
//   get<T>(name: string): T;
// }

// export interface EventTypeStrategyRegistration {
//   type: EventType;
//   strategy: IEventTypeStrategy;
// }

// export type Schedule = "monthly" | "weekly" | "daily" | "hourly";

// export interface CollectorRegistration {
//   create(
//     config: IConfig,
//     recorder: IEventRecorder,
//     cache: TimeSeriesCacheWrapper,
//   ): Promise<ICollector>;

//   name: string;

//   description: string;

//   group: string;

//   schedule: Schedule;

//   artifactScope: ArtifactNamespace[];

//   contributorScope: ContributorNamespace[];
// }

// export class Config implements IConfig {
//   private storage: Record<string, any>;

//   constructor() {
//     this.storage = {};
//   }

//   get<T>(name: string): T {
//     const retVal = this.storage[name];
//     if (retVal === undefined || retVal === null) {
//       throw new Error(`config item ${name} does not exist`);
//     }
//     return retVal as T;
//   }
// }

// /**
//  * Main interface to the indexer.
//  */
// export interface IScheduler {
//   registerEventType(reg: EventTypeStrategyRegistration): void;

//   registerCollector(reg: CollectorRegistration): void;

//   /**
//    * Should process all register collectors and schedule them
//    */
//   schedule(): Promise<void>;

//   execute(): Promise<void>;
// }

// export class BaseScheduler implements IScheduler {
//   private recorder: IEventRecorder;
//   private config: IConfig;
//   private collectors: Record<string, CollectorRegistration>;
//   private eventPointerManager: EventPointerManager;
//   private cache: TimeSeriesCacheWrapper;

//   constructor(
//     recorder: IEventRecorder,
//     config: IConfig,
//     eventPointerManager: EventPointerManager,
//     cache: TimeSeriesCacheWrapper,
//   ) {
//     this.recorder = recorder;
//     this.config = config;
//     this.collectors = {};
//     this.cache = cache;
//     this.eventPointerManager = eventPointerManager;
//   }

//   registerCollector(reg: CollectorRegistration) {
//     this.collectors[reg.name] = reg;
//   }

//   registerEventType(reg: EventTypeStrategyRegistration) {
//     this.recorder.registerEventType(reg.type, reg.strategy);
//   }

//   async schedule(): Promise<void> {
//     // Create new jobs
//     return;
//   }

//   async execute(): Promise<void> {
//     // Execute from the jobs queue.
//     return;
//   }

//   async executeForRange(collectorName: string, range: Range) {
//     const reg = this.collectors[collectorName];

//     this.recorder.setActorScope(reg.artifactScope, reg.contributorScope);
//     const collector = await reg.create(this.config, this.recorder, this.cache);

//     // Get a list of the monitored artifacts
//     for await (const group of collector.groupedArtifacts()) {
//       // Determine anything missing from this group
//       const missing = await this.findMissingArtifactsFromEventPointers(
//         range,
//         group.artifacts,
//         collectorName,
//       );

//       // Nothing missing in this group. Skip
//       if (missing.length === 0) {
//         continue;
//       }

//       // Execute the collection for the missing items
//       await collector.collect(
//         { details: group.details, artifacts: missing },
//         range,
//         async (artifact) => {
//           await this.eventPointerManager.commitArtifactForRange(
//             range,
//             artifact,
//             collectorName,
//           );
//         },
//       );
//       // TODO: Ensure all artifacts are committed or error
//     }
//     await this.recorder.waitAll();
//   }

//   private async findMissingArtifactsFromEventPointers(
//     range: Range,
//     artifacts: Artifact[],
//     collectorName: string,
//   ): Promise<Artifact[]> {
//     const eventPtrs =
//       await this.eventPointerManager.getAllEventPointersForRange(
//         range,
//         artifacts,
//         collectorName,
//       );
//     const existingMap = eventPtrs.reduce<Record<number, Range[]>>((a, c) => {
//       const pointers = a[c.artifactId] || [];
//       pointers.push(rangeFromDates(c.startDate, c.endDate));
//       a[c.artifactId] = pointers;
//       return a;
//     }, {});
//     return artifacts.filter((a) => {
//       const ranges = existingMap[a.id];
//       // If there're no ranges then this is missing events
//       if (!ranges) {
//         return true;
//       }
//       return (
//         findMissingRanges(range.startDate, range.endDate, ranges).length > 0
//       );
//     });
//   }
// }
