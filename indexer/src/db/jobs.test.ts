import { DateTime } from "luxon";
import {
  GroupAlreadyActive,
  JobAlreadyActive,
  JobExecutionRepository,
  JobsRepository,
} from "./jobs.js";
import { clearDb, withDbDescribe } from "./testing.js";
import { AppDataSource } from "./data-source.js";

withDbDescribe("Jobs", () => {
  beforeEach(async () => {
    await clearDb();
  });

  it("should create jobs", async () => {
    const job0 = await JobsRepository.queueJob(
      "collector0",
      null,
      DateTime.now().startOf("day"),
    );
    const job1 = await JobsRepository.queueJob(
      "collector1",
      "group0",
      DateTime.now().startOf("day"),
    );
    const job2 = await JobsRepository.queueJob(
      "collector2",
      "group1",
      DateTime.now().startOf("day"),
    );
    const job3 = await JobsRepository.queueJob(
      "collector3",
      "group1",
      DateTime.now().startOf("day"),
    );
    await JobsRepository.queueJob(
      "collector4",
      null,
      DateTime.now().startOf("day"),
    );

    let availableJobs = await JobsRepository.availableJobGroups();
    expect(availableJobs.length).toBe(4);

    await JobExecutionRepository.createExecutionForJob(job0);

    availableJobs = await JobsRepository.availableJobGroups();
    expect(availableJobs.length).toBe(3);

    await expect(() => {
      return JobExecutionRepository.createExecutionForJob(job0);
    }).rejects.toThrow(JobAlreadyActive);

    await JobExecutionRepository.createExecutionForJob(job1);

    await JobExecutionRepository.createExecutionForJob(job2);

    await expect(() => {
      return JobExecutionRepository.createExecutionForJob(job3);
    }).rejects.toThrow(GroupAlreadyActive);
  });

  afterAll(async () => {
    try {
      await AppDataSource.destroy();
    } catch (_e) {
      console.log("data source already disconnected");
    }
  });
});
