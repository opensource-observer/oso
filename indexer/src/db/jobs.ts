import { AppDataSource } from "./data-source.js";
import {
  Job,
  JobStatus,
  JobExecutionStatus,
  JobExecution,
} from "./orm-entities.js";

export type JobGroup<T> = {
  name: string;
  jobs: T[];
};

export type JobRef = {
  id: number;
  execGroup: string;
  collector: string;
};

/**
 * Jobs repository
 */
export const JobsRepository = AppDataSource.getRepository(Job).extend({
  async availableJobGroups(): Promise<JobGroup<JobRef>[]> {
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
      const group = job.execGroup;
      const groupStorage = groups[group] || [];
      groupStorage.push(job);
      groups[group] = groupStorage;
      return groups;
    }, {});
    const jobGroups: JobGroup<JobRef>[] = [];

    for (const name in groupedJobsByName) {
      const jobs = groupedJobsByName[name];
      if (name == "") {
        jobs.forEach((j) =>
          jobGroups.push({
            name: "",
            jobs: [j],
          }),
        );
      } else {
        // If any of the jobs have an active execution. don't add to the jobGroups
        const hasActiveExecs = jobs.reduce<boolean>((hasActive, current) => {
          if (hasActive) {
            return true;
          }
          if (current.executions.length == 0) {
            return false;
          }
          return current.executions.reduce<boolean>((hasActiveExec, exec) => {
            if (hasActiveExec) {
              return true;
            }
            return exec.status == JobExecutionStatus.ACTIVE;
          }, false);
        }, false);

        if (!hasActiveExecs) {
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
    return await this.create({
      status: JobExecutionStatus.ACTIVE,
      job: job,
    });
  },
});
