import { randomUUID } from "crypto";
import { GenericError } from "../common/errors.js";
import { AppDataSource } from "./data-source.js";
import {
  Job,
  JobStatus,
  JobExecutionStatus,
  JobExecution,
  JobGroupLock,
} from "./orm-entities.js";
import { DateTime } from "luxon";
import { QueryFailedError } from "typeorm";
import type { Brand } from "utility-types";

export class JobAlreadyActive extends GenericError {}
export class JobAlreadyQueued extends GenericError {}
export class GroupAlreadyActive extends GenericError {}

export type JobGrouping<T> = {
  name: string;
  jobs: T[];
};

export type JobRef = {
  id: number;
  group: {
    id?: number;
    name?: string;
  };
  collector: string;
};

export function jobHasActiveExecution(job: Job) {
  if (job.executions.length == 0) {
    return false;
  }
  return job.executions.reduce<boolean>((hasActiveExec, exec) => {
    if (hasActiveExec) {
      return true;
    }
    return exec.status == JobExecutionStatus.ACTIVE;
  }, false);
}

export function jobsHaveActiveExecution(jobs: Job[]) {
  return jobs.reduce<boolean>((hasActive, current) => {
    if (hasActive) {
      return true;
    }
    return jobHasActiveExecution(current);
  }, false);
}

function queryFailedErrorWithDuplicate(err: unknown): boolean {
  if (err instanceof QueryFailedError) {
    if ((err as QueryFailedError).message.indexOf("duplicate") !== -1) {
      return true;
    }
  }
  return false;
}

/**
 * Jobs repository
 */
export const JobsRepository = AppDataSource.getRepository(Job).extend({
  async queueJob(
    collector: string,
    group: string | null,
    scheduledTime: DateTime,
    backfill: boolean,
    options?: Record<string, any>,
  ): Promise<Job> {
    let scheduleType = "main";
    if (backfill) {
      scheduleType = `backfill-${randomUUID()}`;
    }
    const job = this.create({
      group: group,
      scheduledTime: scheduledTime.toJSDate(),
      scheduleType: scheduleType,
      collector: collector,
      status: JobStatus.PENDING,
      options: options,
    });
    try {
      const result = await this.insert(job);
      return await this.findOneOrFail({
        relations: {
          executions: true,
        },
        where: {
          id: result.identifiers[0].id,
        },
      });
    } catch (err) {
      if (queryFailedErrorWithDuplicate(err)) {
        throw new JobAlreadyQueued(
          `Job already queued for this collector at this time`,
        );
      }
      throw err;
    }
  },
  async availableJobGroups(): Promise<JobGrouping<Job>[]> {
    const allIncompleteJobs = await this.find({
      relations: {
        executions: true,
      },
      where: {
        status: JobStatus.PENDING,
      },
    });
    const groupedJobsByName = allIncompleteJobs.reduce<
      Record<string, Array<Job & { executions: JobExecution[] }>>
    >((groups, job) => {
      const group = job.group || "none";
      const groupStorage = groups[group] || [];
      groupStorage.push(job);
      groups[group] = groupStorage;
      return groups;
    }, {});
    const jobGroups: JobGrouping<Job>[] = [];

    for (const name in groupedJobsByName) {
      const jobs = groupedJobsByName[name];

      if (name == "none") {
        jobs.forEach((j) => {
          if (!jobHasActiveExecution(j)) {
            jobGroups.push({
              name: "none",
              jobs: [j],
            });
          }
        });
      } else {
        if (!jobsHaveActiveExecution(jobs)) {
          jobGroups.push({
            name: name,
            jobs: jobs,
          });
        }
      }
    }
    return jobGroups;
  },
});

export const JobExecutionRepository = AppDataSource.getRepository(
  JobExecution,
).extend({
  /**
   * Call this to establish a lock on a job's execution
   *
   * @param ref JobRef for the job to create an execution for
   * @returns
   */
  async createExecutionForJob(job: Job) {
    const hasActive = job.executions.reduce<boolean>((hasActive, current) => {
      if (hasActive) {
        return true;
      }
      return current.status === JobExecutionStatus.ACTIVE;
    }, false);

    if (hasActive) {
      throw new JobAlreadyActive(
        `Job[${job.id}] running "${job.collector}" already has an active execution`,
      );
    }

    const attempt = job.executions.length;

    return this.manager.transaction(async (manager) => {
      const repo = manager.withRepository(this);
      const groupLockRepo = manager.getRepository(JobGroupLock);

      if (job.group) {
        const group = await groupLockRepo.create({
          name: job.group,
        });
        try {
          // This will fail if there's already a lock for the group
          await groupLockRepo.insert(group);
        } catch (err) {
          if (err instanceof QueryFailedError) {
            if ((err as QueryFailedError).message.indexOf("duplicate") === -1) {
              throw err;
            }
            throw new GroupAlreadyActive(`group "${group}" already active`);
          }
        }
      }

      try {
        const created = await repo.insert(
          repo.create({
            status: JobExecutionStatus.ACTIVE,
            job: job,
            attempt: attempt,
          }),
        );
        return repo.findOneOrFail({
          relations: {
            job: true,
          },
          where: {
            id: created.identifiers[0].id,
          },
        });
      } catch (err) {
        if (err instanceof QueryFailedError) {
          if ((err as QueryFailedError).message.indexOf("duplicate") === -1) {
            throw err;
          }
          throw new JobAlreadyActive(
            `Job[${job.id}] running "${job.collector}" already has an active execution`,
          );
        }
      }
    });
  },

  async updateExecutionStatusById(id: number, status: JobExecutionStatus) {
    const execution = await this.findOneOrFail({
      relations: {
        job: true,
      },
      where: {
        id: id as Brand<number, "JobExecutionId">,
      },
    });
    return this.updateExecutionStatus(execution, status);
  },

  async updateExecutionStatus(exec: JobExecution, status: JobExecutionStatus) {
    return this.manager.transaction(async (manager) => {
      const jobRepo = manager.getRepository(Job);
      const repo = manager.withRepository(this);
      const groupLockRepo = manager.getRepository(JobGroupLock);

      const job = await jobRepo.findOneOrFail({
        where: {
          id: exec.job.id,
        },
      });

      if (status === JobExecutionStatus.COMPLETE) {
        // Also mark the job as complete if we've completed this job successfully.
        await jobRepo.update(
          {
            id: job.id,
            version: job.version,
          },
          {
            status: JobStatus.COMPLETE,
          },
        );
      }

      if (job.group) {
        if (
          status === JobExecutionStatus.FAILED ||
          status === JobExecutionStatus.COMPLETE
        ) {
          // Remove any group lock that might exist
          const lock = await groupLockRepo.findOne({
            where: {
              name: job.group,
            },
          });
          if (lock) {
            await groupLockRepo.delete({ id: lock.id });
          }
        }
      }

      // Update the status
      return repo.update(
        {
          id: exec.id,
          version: exec.version,
        },
        {
          status: status,
          version: exec.version + 1,
        },
      );
    });
  },
});
