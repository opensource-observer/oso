import { BigQuery, Dataset } from "@google-cloud/bigquery";
import * as fsPromise from "fs/promises";
import { dedent } from "ts-dedent";
import dayjs from "dayjs";
import { exec } from "child_process";
import * as util from "util";

import { Repo } from "./github.js";
import { logger } from "./utils/logger.js";
import { App, Octokit } from "octokit";
import { CheckConclusion, CheckStatus, setCheckStatus } from "./checks.js";

const execPromise = util.promisify(exec);

export class PRTestDeployCoordinator {
  private bq: BigQuery;
  private repo: Repo;
  private projectId: string;
  private app: App;
  private octo: Octokit;

  constructor(
    repo: Repo,
    app: App,
    octo: Octokit,
    bq: BigQuery,
    projectId: string,
  ) {
    this.bq = bq;
    this.app = app;
    this.repo = repo;
    this.projectId = projectId;
    this.octo = octo;
  }

  async setup(
    pr: number,
    sha: string,
    profilePath: string,
    serviceAccountPath: string,
    checkoutPath: string,
  ) {
    // This should create a new public dataset inside a "testing" project
    // specifically for a pull request
    //
    // This project is intended to be only used to push the last 2 days worth of
    // data into a dev environment
    //
    // The service account associated with this account should only have access to
    // bigquery no other resources. The service account should also continously be
    // rotated. So the project in use should have a very short TTL on service
    // account keys.
    logger.info({
      mesage: "setting up test deployment dataset",
      pr: pr,
      repo: this.repo,
    });

    const datasetName = this.datasetNameFromPR(pr);

    await this.getOrCreateDataset(datasetName);
    await this.generateDbtProfile(datasetName, profilePath, serviceAccountPath);

    // Run dbt
    try {
      await this.runDbt(checkoutPath);
    } catch (e) {
      logger.error({
        message: "error running dbt",
        error: e,
      });
      const err = e as Error;

      await this.failCheckStatus(sha);

      await this.leaveDeploymentComment(
        pr,
        dedent`
        Test deployment for PR #${pr} failed on comment \`${sha}\`. With error: 

        \`\`\`
        ${err.stack}
        \`\`\`
      `,
      );

      return;
    }
    const datasetFQN = `${this.projectId}.${datasetName}`;

    await this.completeCheckStatus(sha, datasetFQN);

    await this.leaveDeploymentComment(
      pr,
      dedent`
      Test deployment for PR #${pr} successfully deployed to \`${datasetFQN}\`.
    `,
    );
  }

  async teardown(pr: number) {
    // Generally this should be called from a pull_request_target "closed" event
    // This will delete a pull request's test deployment
    logger.info({
      message: "tearing down deployment dataset",
      pr: pr,
      repo: this.repo,
    });

    await this.deleteDataset(this.datasetNameFromPR(pr));
  }

  async clean(ttlSeconds: number) {
    const now = dayjs();
    const expiration = now.subtract(ttlSeconds, "seconds");
    logger.info({
      message: "cleaning old datasets",
      expiration: expiration.toISOString(),
    });

    const datasets = await this.listOldDatasets(expiration);

    for (const dataset of datasets) {
      const [ds] = await dataset.get();
      logger.info({
        message: "deleting dataset",
        dataset: ds.id,
      });
      await this.deleteDataset(ds.id);
    }
  }

  private datasetNameFromPR(pr: number) {
    return `pr_${pr}`;
  }

  private async getOrCreateDataset(name: string) {
    const datasetRef = this.bq.dataset(name);
    const [datasetExists] = await datasetRef.exists();

    if (datasetExists) {
      logger.info("found existing");
      const [metadata] = await datasetRef.getMetadata();
      const labels = metadata.labels;
      labels.last_updated = this.generateLastUpdated();
      await datasetRef.setMetadata(metadata);
      logger.info({
        message: "data set already exists. updated last_updated label",
        dataset: name,
        lastUpdated: labels.last_updated,
      });
      return;
    }

    logger.info({
      message: "creating new dataset",
      dataset: name,
    });

    await this.bq.createDataset(name, {
      labels: {
        last_updated: this.generateLastUpdated(),
      },
    });
    return;
  }

  private generateLastUpdated() {
    return `${dayjs().unix()}`;
  }

  private lastUpdatedToObj(s: string) {
    return dayjs.unix(parseInt(s));
  }

  private async deleteDataset(name: string) {
    const datasetRef = this.bq.dataset(name);

    if (!(await datasetRef.exists())) {
      logger.info({
        message: "dataset does not exist. nothing to delete",
        dataset: name,
      });
      return;
    }
    try {
      await datasetRef.delete();
    } catch (e) {
      // Errors are assumed to mean that the dataset doesn't exist for now
      logger.error({
        message: "Encountered error deleting",
        dataset: name,
        error: e,
      });
    }
  }

  private async listOldDatasets(expiration: dayjs.Dayjs) {
    const [datasets] = await this.bq.getDatasets();
    const oldDatasets: Dataset[] = [];
    for (const dataset of datasets) {
      const [metadata] = await dataset.getMetadata();
      if (!metadata.labels.last_updated) {
        logger.warn({
          message: "found a dataset without a last_updated label",
          dataset: dataset.id,
          metadataId: metadata.id,
          metadata: metadata,
        });
        continue;
      }

      const lastUpdated = this.lastUpdatedToObj(metadata.labels.last_updated);
      if (lastUpdated.isBefore(expiration)) {
        oldDatasets.push(dataset);
      }
    }
    return oldDatasets;
  }

  private async generateDbtProfile(
    datasetName: string,
    profilePath: string,
    serviceAccountPath: string,
  ) {
    const contents = dedent`
    opensource_observer:
      target: playground
      outputs:
        playground:
          type: bigquery
          dataset: ${datasetName}
          job_execution_time_seconds: 300
          job_retries: 1
          location: US
          method: service-account
          keyfile: ${serviceAccountPath}
          project: ${this.projectId}
          threads: 32

    `;
    return await fsPromise.writeFile(profilePath, contents);
  }

  private async runDbt(path: string) {
    await execPromise("poetry run dbt run", {
      cwd: path,
      env: {
        PLAYGROUND_DAYS: "1",
      },
    });
  }

  private async leaveDeploymentComment(pr: number, message: string) {
    return this.octo.rest.issues.createComment({
      owner: this.repo.owner,
      repo: this.repo.name,
      body: message,
      issue_number: pr,
    });
  }

  private async completeCheckStatus(sha: string, datasetFQN: string) {
    return setCheckStatus(this.octo, this.repo.owner, this.repo.name, {
      name: "test-deploy",
      head_sha: sha,
      status: CheckStatus.Completed,
      conclusion: CheckConclusion.Success,
      output: {
        title: "Test Deployment Complete",
        summary: `Test deployment available at ${datasetFQN}`,
      },
    });
  }

  private async failCheckStatus(sha: string) {
    return setCheckStatus(this.octo, this.repo.owner, this.repo.name, {
      name: "test-deploy",
      head_sha: sha,
      status: CheckStatus.Completed,
      conclusion: CheckConclusion.Failure,
      output: {
        title: "Test Deployment Failed",
        summary: `Test deployment failed to deploy`,
      },
    });
  }
}
