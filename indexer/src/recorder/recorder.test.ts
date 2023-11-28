import { DateTime } from "luxon";
import { EventRepository } from "../db/events.js";
import {
  ArtifactId,
  ArtifactNamespace,
  ArtifactType,
  EventType,
  RecorderTempDuplicateEvent,
  Recording,
} from "../db/orm-entities.js";
import { withDbDescribe } from "../db/testing.js";
import { BatchEventRecorder, IFlusher } from "./recorder.js";
import { IncompleteEvent, RecordHandle } from "./types.js";
import {
  AppDataSource,
  createAndConnectDataSource,
} from "../db/data-source.js";
import { randomInt, randomUUID } from "node:crypto";
import _ from "lodash";
import { createClient } from "redis";
import { ArtifactRepository } from "../db/artifacts.js";

type Callback = () => void;

class TestFlusher implements IFlusher {
  flushCallback: Callback | undefined;
  lastNotify: number;

  clear(): void {}

  flush(): void {
    if (this.flushCallback) {
      this.flushCallback();
    }
  }

  onFlush(cb: () => void): void {
    this.flushCallback = cb;
  }

  notify(size: number): void {
    this.lastNotify = size;
  }
}

type RandomCommitEventOptions = {
  fromProbability: number;
  repoNameGenerator: () => string;
  usernameGenerator: () => string;
};

function randomCommitEventsGenerator(
  count: number,
  options?: Partial<RandomCommitEventOptions>,
): IncompleteEvent[] {
  const opts: RandomCommitEventOptions = _.merge(
    {
      fromProbability: 1,
      repoNameGenerator: () => `repo-${randomUUID()}`,
      usernameGenerator: () => `user-${randomUUID()}`,
    },
    options,
  );

  const events: IncompleteEvent[] = [];

  for (let i = 0; i < count; i++) {
    const randomToRepoName = opts.repoNameGenerator();
    const randomFromUsername = opts.usernameGenerator();
    const randomTime = DateTime.now()
      .minus({ days: 10 })
      .plus({ minutes: randomInt(14400) });
    const randomSourceId = randomUUID();
    const event: IncompleteEvent = {
      time: randomTime,
      type: {
        version: 1,
        name: "COMMIT_CODE",
      },
      to: {
        type: ArtifactType.GIT_REPOSITORY,
        name: randomToRepoName,
        namespace: ArtifactNamespace.GITHUB,
      },
      sourceId: randomSourceId,
      amount: 1,
      details: {},
    };
    // probabilistically add a from field
    if (Math.random() > 1.0 - opts.fromProbability) {
      event.from = {
        type: ArtifactType.GITHUB_USER,
        name: randomFromUsername,
        namespace: ArtifactNamespace.GITHUB,
      };
    }
    events.push(event);
  }
  return events;
}

withDbDescribe("BatchEventRecorder", () => {
  let flusher: TestFlusher;
  let redisClient: ReturnType<typeof createClient>;
  beforeEach(async () => {
    flusher = new TestFlusher();
    redisClient = createClient({
      url: "redis://redis:6379",
    });
    await redisClient.connect();
  });

  afterEach(async () => {
    await redisClient.flushAll();
    await redisClient.disconnect();
  });

  it("should setup the recorder", async () => {
    const recorder = new BatchEventRecorder(
      AppDataSource,
      [],
      AppDataSource.getRepository(Recording),
      AppDataSource.getRepository(EventType),
      () => Promise.resolve(redisClient),
      {
        maxBatchSize: 3,
        timeoutMs: 30000,
        flusher: flusher,
      },
    );
    await recorder.loadEventTypes();
    recorder.setRange({
      startDate: DateTime.now().minus({ month: 1 }),
      endDate: DateTime.now().plus({ month: 1 }),
    });
    recorder.setActorScope(
      [ArtifactNamespace.GITHUB],
      [ArtifactType.GITHUB_USER, ArtifactType.GIT_REPOSITORY],
    );
    const testEvent: IncompleteEvent = {
      amount: Math.random(),
      time: DateTime.now(),
      type: {
        name: "COMMIT_CODE",
        version: 1,
      },
      to: {
        name: "test",
        namespace: ArtifactNamespace.GITHUB,
        type: ArtifactType.GIT_REPOSITORY,
      },
      from: {
        name: "contributor",
        namespace: ArtifactNamespace.GITHUB,
        type: ArtifactType.GITHUB_USER,
      },
      sourceId: "test123",
    };

    await recorder.begin();

    await recorder.record(testEvent);
    //flusher.flush();
    await recorder.commit();

    // Check that the values are correct
    const results = await EventRepository.find();
    expect(results.length).toEqual(1);
    expect(results[0].sourceId).toEqual(testEvent.sourceId);
    expect(results[0].amount).toEqual(testEvent.amount);
    expect(results[0].fromId).toBeDefined();
    expect(results[0].toId).toBeDefined();

    const toArtifact = await ArtifactRepository.findOneByOrFail({
      id: results[0].toId as ArtifactId,
    });
    const fromArtifact = await ArtifactRepository.findOneByOrFail({
      id: results[0].fromId as ArtifactId,
    });

    expect(toArtifact.name).toEqual(testEvent.to.name);
    expect(toArtifact.namespace).toEqual(testEvent.to.namespace);
    expect(toArtifact.type).toEqual(testEvent.to.type);

    expect(fromArtifact.name).toEqual(testEvent.from?.name);
    expect(fromArtifact.namespace).toEqual(testEvent.from?.namespace);
    expect(fromArtifact.type).toEqual(testEvent.from?.type);
  });

  describe("various recorder scenarios", () => {
    let recorder: BatchEventRecorder;
    let testEvent: IncompleteEvent;
    let errors: unknown[];
    beforeEach(async () => {
      errors = [];
      recorder = new BatchEventRecorder(
        AppDataSource,
        [
          await createAndConnectDataSource("test1"),
          await createAndConnectDataSource("test2"),
          await createAndConnectDataSource("test3"),
          await createAndConnectDataSource("test4"),
          await createAndConnectDataSource("test5"),
        ],
        AppDataSource.getRepository(Recording),
        AppDataSource.getRepository(EventType),
        () => Promise.resolve(redisClient),
        {
          maxBatchSize: 100000,
          flushIntervalMs: 1000,
          timeoutMs: 300000,
        },
      );
      await recorder.loadEventTypes();
      recorder.setRange({
        startDate: DateTime.now().minus({ month: 1 }),
        endDate: DateTime.now().plus({ month: 1 }),
      });
      recorder.setActorScope(
        [ArtifactNamespace.GITHUB],
        [ArtifactType.GITHUB_USER, ArtifactType.GIT_REPOSITORY],
      );
      recorder.addListener("error", (err) => {
        errors.push(err);
      });
      testEvent = {
        amount: Math.random(),
        time: DateTime.now(),
        type: {
          name: "COMMIT_CODE",
          version: 1,
        },
        to: {
          name: "test",
          namespace: ArtifactNamespace.GITHUB,
          type: ArtifactType.GIT_REPOSITORY,
        },
        from: {
          name: "contributor",
          namespace: ArtifactNamespace.GITHUB,
          type: ArtifactType.GITHUB_USER,
        },
        sourceId: "test123",
      };
      await recorder.begin();
      await recorder.record(testEvent);
    });

    afterEach(async () => {
      await recorder.close();
    });

    // In the current iteration of the recorder, dupes aren't errors. skipping
    // for now.
    it.skip("should fail when trying to write a duplicate event", async () => {
      const dupeRepo = AppDataSource.getRepository(RecorderTempDuplicateEvent);

      const dupes = await dupeRepo.find();
      expect(dupes.length).toEqual(1);

      const errs: unknown[] = [];
      recorder.addListener("error", (err) => {
        errs.push(err);
      });

      // An error should be thrown if we attempt to write the same event twice.
      // This should be considered a failure of the collector.
      await recorder.record(testEvent);
      const handle = await recorder.record(randomCommitEventsGenerator(1)[0]);
      await recorder.wait([handle]);

      expect(errs.length).toEqual(1);
    });

    it("should do a large set of writes", async () => {
      const eventCountToWrite = 1000000;
      const events = randomCommitEventsGenerator(eventCountToWrite, {
        fromProbability: 0.7,
        repoNameGenerator: () => `repo-${randomInt(100)}`,
        usernameGenerator: () => `user-${randomInt(10000)}`,
      });
      const handles: RecordHandle[] = [];
      for (const event of events) {
        handles.push(await recorder.record(event));
      }
      const completion = recorder.wait(handles);
      await recorder.commit();
      await completion;

      // Check that the events are in the database
      const eventCount = await EventRepository.count();
      expect(eventCount).toEqual(eventCountToWrite + 1);
    }, 300000);

    it("should try to write duplicates", async () => {
      const eventCountToWrite = 10;
      const events = randomCommitEventsGenerator(eventCountToWrite, {
        fromProbability: 0.7,
        repoNameGenerator: () => `repo-${randomInt(100)}`,
        usernameGenerator: () => `user-${randomInt(10000)}`,
      });
      const handles: RecordHandle[] = [];
      for (const event of events) {
        handles.push(await recorder.record(event));
      }
      // Try to dupe
      for (const event of events.slice(0, eventCountToWrite / 2)) {
        handles.push(await recorder.record(event));
      }
      const completion = recorder.wait(handles);
      const results = await recorder.commit();
      await completion;

      // Check that the events are in the database
      const eventCount = await EventRepository.count();
      expect(eventCount).toEqual(eventCountToWrite / 2 + 1);
      expect(results.committed.length).toEqual(6);

      expect(results.invalid.length).toEqual(5);
    }, 60000);

    // In the current iteration of the recorder, dupes aren't errors. skipping
    // for now.
    it.skip("should record errors when we write some duplicates over multiple batches", async () => {
      const events = randomCommitEventsGenerator(10);

      const errs: unknown[] = [];

      recorder.addListener("error", (err) => {
        errs.push(err);
      });

      let handles: RecordHandle[] = [];
      for (const event of events) {
        handles.push(await recorder.record(event));
      }
      const results0 = await recorder.wait(handles);
      expect(results0.errors.length).toEqual(0);

      // Add an event for this test to pass
      events.push(...randomCommitEventsGenerator(1));

      // Try to write them again
      handles = [];
      for (const event of events) {
        handles.push(await recorder.record(event));
      }

      await recorder.wait(handles);
      expect(errs.length).toEqual(10);
    });
  });
});
