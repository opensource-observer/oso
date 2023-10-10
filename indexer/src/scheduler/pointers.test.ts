import { DateTime } from "luxon";
import { ArtifactRepository } from "../db/artifacts.js";
import { EventPointerRepository } from "../db/events.js";
import { withDbDescribe } from "../db/testing.js";
import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  EventPointer,
} from "../index.js";
import { EventPointerManager } from "./pointers.js";
import { AppDataSource } from "../db/data-source.js";
import { rangeFromISO, Range } from "../utils/ranges.js";

withDbDescribe("EventPointerManager", () => {
  let artifact0: Artifact;
  let eventPointer0: EventPointer;
  let eventPointer1: EventPointer;
  let eventPointers: EventPointer[];
  let manager: EventPointerManager;

  beforeEach(async () => {
    // Setup the database
    artifact0 = await ArtifactRepository.save(
      ArtifactRepository.create({
        name: "test0",
        namespace: ArtifactNamespace.OPTIMISM,
        type: ArtifactType.CONTRACT_ADDRESS,
      }),
    );

    eventPointer0 = await EventPointerRepository.save(
      EventPointerRepository.create({
        artifact: artifact0,
        collector: "test",
        startDate: DateTime.fromISO("2023-01-01T00:00:00Z").toJSDate(),
        endDate: DateTime.fromISO("2023-02-01T00:00:00Z").toJSDate(),
        version: 0,
      }),
    );

    eventPointer1 = await EventPointerRepository.save(
      EventPointerRepository.create({
        artifact: artifact0,
        collector: "test",
        startDate: DateTime.fromISO("2023-03-01T00:00:00Z").toJSDate(),
        endDate: DateTime.fromISO("2023-04-01T00:00:00Z").toJSDate(),
        version: 0,
      }),
    );

    eventPointers = [eventPointer0, eventPointer1];

    manager = new EventPointerManager(AppDataSource, EventPointerRepository);
  });

  function itWithEventPointers(
    message: string,
    range: Range,
    expectedPointerIndexes: number[],
  ) {
    it(message, async () => {
      const expectedMatches = expectedPointerIndexes.map(
        (n) => eventPointers[n],
      );
      const result = await manager.getAllEventPointersForRange("test", range, [
        artifact0,
      ]);
      expect(result.length).toBe(expectedMatches.length);
      const sortedResultIds = result.map((e) => e.id.valueOf());
      const sortedExpectedIds = expectedMatches.map((e) => e.id.valueOf());
      sortedResultIds.sort();
      sortedExpectedIds.sort();
      expect(sortedResultIds).toEqual(sortedExpectedIds);
    });
  }

  itWithEventPointers(
    "should match exactly with existing pointer",
    rangeFromISO("2023-01-01T00:00:00Z", "2023-02-01T00:00:00Z"),
    [0],
  );

  itWithEventPointers(
    "should match existing pointer that starts before range starts and ends before the range ends",
    rangeFromISO("2023-01-05T00:00:00Z", "2023-02-05T00:00:00Z"),
    [0],
  );

  itWithEventPointers(
    "should match existing pointer that starts after the range starts and ends after the range ends",
    rangeFromISO("2023-01-05T00:00:00Z", "2023-02-05T00:00:00Z"),
    [0],
  );

  itWithEventPointers(
    "should match with larger pointer",
    rangeFromISO("2023-01-02T00:00:00Z", "2023-01-10T00:00:00Z"),
    [0],
  );

  itWithEventPointers(
    "should match with a smaller pointer",
    rangeFromISO("2022-12-31T00:00:00Z", "2023-02-02T00:00:00Z"),
    [0],
  );

  itWithEventPointers(
    "should match with multiple pointers",
    rangeFromISO("2022-01-15T00:00:00Z", "2023-03-02T00:00:00Z"),
    [0, 1],
  );

  itWithEventPointers(
    "should not match with a pointer - range is before any pointers",
    rangeFromISO("2022-12-31T00:00:00Z", "2023-01-01T00:00:00Z"),
    [],
  );

  it("should merge pointers together", async () => {
    const range = rangeFromISO("2022-01-15T00:00:00Z", "2023-03-02T00:00:00Z");
    await manager.commitArtifactForRange("test", range, artifact0);

    // Check that there's only a single pointer left
    const result = await manager.getAllEventPointersForRange("test", range, [
      artifact0,
    ]);
    expect(result.length).toBe(1);
  });

  it("should merge pointers together when they do not intersect", async () => {
    const range = rangeFromISO("2023-04-01T00:00:00Z", "2023-05-01T00:00:00Z");
    await manager.commitArtifactForRange("test", range, artifact0);

    // Check that there's only a single pointer left
    const totalRange = rangeFromISO(
      "2023-02-02T00:00:00Z",
      "2023-05-01T00:00:00Z",
    );
    const result = await manager.getAllEventPointersForRange(
      "test",
      totalRange,
      [artifact0],
    );
    expect(result.length).toBe(1);
    expect(
      DateTime.fromJSDate(result[0].startDate)
        .toUTC()
        .toISO({ suppressMilliseconds: true }),
    ).toEqual("2023-03-01T00:00:00Z");
  });
});
