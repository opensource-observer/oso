import { DateTime } from "luxon";
import { ArtifactRepository } from "../db/artifacts.js";
import { AppDataSource } from "../db/data-source.js";
import { EventRepository } from "../db/events.js";
import {
  ArtifactNamespace,
  ArtifactType,
  EventType,
} from "../db/orm-entities.js";
import { clearDb, withDbDescribe } from "../db/testing.js";
import { BatchEventRecorder } from "./recorder.js";
import { generateEventTypeStrategy } from "./types.js";

withDbDescribe("BatchEventRecorder", () => {
  beforeEach(async () => {
    await clearDb();
  });

  it("should setup the recorder", async () => {
    const recorder = new BatchEventRecorder(
      EventRepository,
      ArtifactRepository,
      {
        maxBatchSize: 3,
      },
    );
    recorder.registerEventType(
      EventType.COMMIT_CODE,
      generateEventTypeStrategy(EventType.COMMIT_CODE),
    );
    recorder.setActorScope(
      [ArtifactNamespace.GITHUB],
      [ArtifactType.GITHUB_USER, ArtifactType.GIT_REPOSITORY],
    );
    const testEvent = {
      amount: Math.random(),
      time: DateTime.now(),
      type: EventType.COMMIT_CODE,
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
    recorder.record(testEvent);
    await recorder.wait(EventType.COMMIT_CODE);

    // No errors should be thrown if we attempt to write twice
    recorder.record(testEvent);
    await recorder.wait(EventType.COMMIT_CODE);

    // Check that the values are correct
    const results = await EventRepository.find({
      relations: {
        to: true,
        from: true,
      },
      where: {
        type: EventType.COMMIT_CODE,
      },
    });
    expect(results.length).toEqual(1);
    expect(results[0].sourceId).toEqual(testEvent.sourceId);
    expect(results[0].amount).toEqual(testEvent.amount);
    expect(results[0].to.name).toEqual(testEvent.to.name);
    expect(results[0].to.namespace).toEqual(testEvent.to.namespace);
    expect(results[0].to.type).toEqual(testEvent.to.type);
    expect(results[0].to.id).toBeDefined();
    expect(results[0].from?.name).toEqual(testEvent.from.name);
    expect(results[0].from?.namespace).toEqual(testEvent.from.namespace);
    expect(results[0].from?.type).toEqual(testEvent.from.type);
    expect(results[0].from?.id).toBeDefined();
  });

  afterAll(async () => {
    try {
      await AppDataSource.destroy();
    } catch (_e) {
      console.log("data source already disconnected");
    }
  });
});
