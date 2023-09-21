import {
  PrismaClient,
  Job,
  JobStatus,
  JobExecutionStatus,
  JobExecution,
} from "@prisma/client";

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
export class JobsRepository {
  private prisma: PrismaClient;

  constructor(prisma: PrismaClient) {
    this.prisma = prisma;
  }

  async availableJobGroups(): Promise<JobGroup<JobRef>[]> {
    const allIncompleteJobs = await this.prisma.job.findMany({
      include: {
        executions: true,
      },
      where: {
        status: {
          equals: JobStatus.PENDING,
        },
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
  }

  /**
   * Call this to establish a lock on a job's execution
   *
   * @param ref JobRef for the job to create an execution for
   * @returns
   */
  async createExecutionForJob(ref: JobRef) {
    return await this.prisma.jobExecution.createMany({
      data: {
        status: JobExecutionStatus.ACTIVE,
        jobId: ref.id,
      },
    });
  }
}
