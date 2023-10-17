import { BulkUpdateBySourceIDEvent, EventRepository } from "./events.js";
import { ArtifactRepository } from "./artifacts.js";
import { withDbDescribe } from "./testing.js";
import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
  EventType,
} from "./orm-entities.js";
import { AppDataSource } from "./data-source.js";

withDbDescribe("EventRepository", () => {
  let artifact0: Artifact;
  let artifact1: Artifact;
  let eventType: EventType;

  beforeEach(async () => {
    // Setup the database
    artifact0 = await ArtifactRepository.save(
      ArtifactRepository.create({
        name: "test0",
        namespace: ArtifactNamespace.OPTIMISM,
        type: ArtifactType.CONTRACT_ADDRESS,
      }),
    );

    artifact1 = await ArtifactRepository.save(
      ArtifactRepository.create({
        name: "test1",
        namespace: ArtifactNamespace.OPTIMISM,
        type: ArtifactType.CONTRACT_ADDRESS,
      }),
    );

    eventType = await AppDataSource.getRepository(EventType).findOneOrFail({
      where: {
        name: "CONTRACT_INVOKED",
      },
    });
  });

  it("should update the events based on sourceId", async () => {
    // Setup some events
    const createPartials: BulkUpdateBySourceIDEvent[] = [
      {
        time: new Date(),
        sourceId: "0",
        to: artifact0,
        type: eventType,
        amount: 1,
        from: null,
      },
      {
        time: new Date(),
        sourceId: "1",
        to: artifact0,
        type: eventType,
        amount: 1,
        from: null,
      },
      {
        time: new Date(),
        sourceId: "2",
        to: artifact0,
        type: eventType,
        amount: 2,
        from: null,
      },
      {
        time: new Date(),
        sourceId: "3",
        to: artifact0,
        type: eventType,
        amount: 3,
        from: null,
      },
      {
        time: new Date(),
        sourceId: "4",
        to: artifact0,
        type: eventType,
        amount: 4,
        from: null,
      },
    ];
    const events = EventRepository.create(createPartials);
    await EventRepository.insert(events);

    const beforeUpdate = await Promise.all(
      events.map((e) => {
        return EventRepository.findOneOrFail({
          relations: {
            to: true,
            from: true,
          },
          where: {
            sourceId: e.sourceId,
          },
        });
      }),
    );

    const updatePartials: BulkUpdateBySourceIDEvent[] = [
      {
        time: createPartials[0].time,
        sourceId: "0",
        to: artifact0,
        type: eventType,
        amount: -100,
        from: null,
      },
      {
        time: createPartials[1].time,
        sourceId: "1",
        to: artifact1,
        type: eventType,
        amount: 2,
        from: null,
      },
      {
        time: createPartials[2].time,
        sourceId: "2",
        to: artifact0,
        type: eventType,
        amount: 4,
        from: artifact1,
      },
      {
        time: new Date(),
        sourceId: "4",
        to: artifact0,
        type: eventType,
        amount: 8,
        from: null,
      },
    ];

    await EventRepository.bulkUpdateBySourceIDAndType(updatePartials);

    const afterUpdate = await Promise.all(
      events.map((e) => {
        return EventRepository.findOneOrFail({
          relations: {
            to: true,
            from: true,
          },
          where: {
            sourceId: e.sourceId,
          },
        });
      }),
    );

    expect(beforeUpdate.map((e) => e.sourceId)).toEqual(
      afterUpdate.map((e) => e.sourceId),
    );

    expect(beforeUpdate[0].amount).toEqual(1);
    expect(afterUpdate[0].amount).toEqual(-100);

    expect(afterUpdate[1].amount).toEqual(2);
    expect(afterUpdate[1]).toHaveProperty("to.id", artifact1.id);
    expect(afterUpdate[2]).toHaveProperty("from.id", artifact1.id);
  });
});
