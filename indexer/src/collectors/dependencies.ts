import { Repository } from "typeorm";
import { CollectResponse, IPeriodicCollector } from "../scheduler/types.js";
import { Artifact, ArtifactType, Collection } from "../index.js";
import { BigQuery } from "@google-cloud/bigquery";
import { sha1FromArray } from "../utils/source-ids.js";
import { logger } from "../utils/logger.js";
import { TransformCallback, TransformOptions, Writable } from "stream";

type DependentRawRow = {
  package_name: string;
  dependent_name: string;
  depth_name: number;
};

class DependentsRecorder extends Writable {
  private collectionRepository: Repository<Collection>;
  private batchCount: number;
  private batchSize: number;

  constructor(
    collectionRepository: Repository<Collection>,
    batchSize: number,
    opts?: TransformOptions,
  ) {
    super({
      ...{
        objectMode: true,
        readableObjectMode: true,
        writableObjectMode: true,
      },
      ...opts,
    });
    this.collectionRepository = collectionRepository;
    this.batchCount = 0;
  }

  _write(
    row: DependentRawRow,
    encoding: BufferEncoding,
    done: TransformCallback,
  ): void {
    done();
  }

  async getTemporaryCollection() {}
}

export class DependentsPeriodicCollector implements IPeriodicCollector {
  private artifactRepository: Repository<Artifact>;
  private collectionRepository: Repository<Collection>;
  private bq: BigQuery;
  private datasetId: string;

  constructor(
    artifactRepository: Repository<Artifact>,
    collectionRepository: Repository<Collection>,
    bq: BigQuery,
    datasetId: string,
  ) {
    this.artifactRepository = artifactRepository;
    this.collectionRepository = collectionRepository;
    this.datasetId = datasetId;
    this.bq = bq;
  }

  async ensureDataset() {
    const ds = this.bq.dataset(this.datasetId);

    if (!(await ds.exists())) {
      throw new Error(
        `dataset ${this.datasetId} does not exist. please create it`,
      );
    }
    return ds;
  }

  async collect(): Promise<CollectResponse> {
    logger.debug("collecting dependents for all npm packages");

    // Get a list of all `NPM_PACKAGES` in our database
    const npmPackages = await this.artifactRepository.find({
      where: {
        type: ArtifactType.NPM_PACKAGE,
      },
      order: {
        id: { direction: "ASC" },
      },
    });

    try {
      const dependents = await this.getOrCreateDependentsTable(npmPackages);
      await new Promise<void>((resolve, reject) => {
        dependents
          .createReadStream({ autoPaginate: true })
          .pipe(
            new DependentsRecorder(this.collectionRepository, {
              highWaterMark: 1000,
            }),
          )
          .on("end", () => {
            resolve();
          })
          .on("error", (err) => {
            reject(err);
          });
      });
    } catch (err) {
      logger.error(`caught error collecting dependencies`, JSON.stringify(err));
      throw err;
    }
  }

  private async getOrCreateDependentsTable(packages: Artifact[]) {
    const packagesSha1 = sha1FromArray(
      packages.map((a) => {
        return `${a.id},${a.name}`;
      }),
    );

    // Check if the dataset's table already exists
    const tableId = `npm_${packagesSha1}`;

    logger.debug(`checking for table ${tableId}`);

    const dataset = await this.ensureDataset();
    const destinationTable = dataset.table(tableId);

    const [destinationTableExists] = await destinationTable.exists();
    if (destinationTableExists) {
      logger.debug("table exists. no need to query BQ");
      return destinationTable;
    }

    // Query the bigquery public dataset into a temporary table
    //
    // TODO: For now this is hardcoded to the snapshot of deps from 2023-10-16
    // to reduce the number of results to scan on BQ
    const query = `
      SELECT 
        Name as package_name, 
        Dependent.Name as dependent_name,
        MinimumDepth as minimum_depth
      FROM 
        \`bigquery-public-data.deps_dev_v1.Dependents\` 
      WHERE 
        TIMESTAMP_TRUNC(SnapshotAt, DAY) = TIMESTAMP('2023-10-16')
        AND System = 'NPM'
        AND Lower(Name) IN UNNEST(@packages)
        AND Lower(Dependent.Name) IN UNNEST(@packages)
        AND MinimumDepth < 5
    `;

    const options = {
      query: query,
      location: "US",
      destination: destinationTable,
      params: {
        packages: packages.map((a) => a.name),
      },
    };
    const [job] = await this.bq.createQueryJob(options);
    // Wait for the job to complete
    await job.getQueryResults({ maxResults: 0 });
    logger.debug(`biqquery job complete`);
    return destinationTable;
  }
}
