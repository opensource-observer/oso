import { In, Repository } from "typeorm";
import { CollectResponse, IPeriodicCollector } from "../scheduler/types.js";
import { Artifact, ArtifactType, Collection } from "../index.js";
import { BigQuery } from "@google-cloud/bigquery";
import { sha1FromArray } from "../utils/source-ids.js";
import { logger } from "../utils/logger.js";
import { TransformCallback, TransformOptions, Writable } from "stream";
import { randomUUID } from "crypto";
import { CollectionType, Project } from "../db/orm-entities.js";
import _ from "lodash";
import { UniqueArray } from "../utils/array.js";

type DependentRawRow = {
  package_name: string;
  dependent_name: string;
  minimum_depth: number;
};

type CollectionQueueStorage = {
  name: string;
  collection: Collection;
  relations: UniqueArray<Project>;
};

class DependentsRecorder extends Writable {
  private collectionRepository: Repository<Collection>;
  private collectionTypeRepository: Repository<CollectionType>;
  private projectRepository: Repository<Project>;
  private batchSize: number;
  private batch: DependentRawRow[];
  private packages: Artifact[];
  private uuid: string;
  private packageMap: Record<string, Artifact>;
  private tempCollectionQueue: Record<string, CollectionQueueStorage>;
  private collectionTypes: Record<string, CollectionType>;
  private artifactNameToProjectsMap: Record<string, UniqueArray<Project>>;

  constructor(
    packages: Artifact[],
    collectionRepository: Repository<Collection>,
    collectionTypeRepository: Repository<CollectionType>,
    projectRepository: Repository<Project>,
    batchSize: number,
    opts?: TransformOptions,
  ) {
    super({
      ...{
        objectMode: true,
        readableObjectMode: true,
        writableObjectMode: true,
        highWaterMark: 1,
      },
      ...opts,
    });
    this.batchSize = batchSize;
    this.collectionRepository = collectionRepository;
    this.collectionTypeRepository = collectionTypeRepository;
    this.projectRepository = projectRepository;
    this.batch = [];
    this.packages = packages;
    this.uuid = randomUUID();
    this.tempCollectionQueue = {};
    this.collectionTypes = {};
    this.artifactNameToProjectsMap = {};
    this.packageMap = _.keyBy(packages, "name");
  }

  _write(
    row: DependentRawRow,
    _encoding: BufferEncoding,
    done: TransformCallback,
  ): void {
    logger.debug(`${row.package_name} -> ${row.dependent_name}`);
    if (row !== null) {
      this.batch.push(row);
    }

    if (this.batch.length < this.batchSize && row !== null) {
      done();
      return;
    } else {
      // Save things to the db
      this.writeBatch()
        .then(() => {
          if (row === null) {
            this.commitAll()
              .then(() => {
                done();
              })
              .catch((err) => {
                done(err);
              });
          } else {
            done();
          }
        })
        .catch((err) => {
          done(err);
        });
    }
  }

  _final(done: (error?: Error | null | undefined) => void): void {
    logger.debug("Committing all temporary collections");
    this.commitAll()
      .then(() => {
        done();
      })
      .catch((err) => {
        done(err);
      });
  }

  async commitAll() {
    // In a transaction delete the old collection if it exists and rename the current one
    for (const name in this.tempCollectionQueue) {
      const queueStorage = this.tempCollectionQueue[name];
      const collection = queueStorage.collection;

      await this.collectionRepository.manager.transaction(async (manager) => {
        const repo = manager.withRepository(this.collectionRepository);

        // Find the canonical one if it exists
        const artifact = collection.artifactOwner;
        if (!artifact) {
          throw new Error(
            "invalid temporary collection. it has no artifact owner",
          );
        }
        const canonicalSlug =
          `${artifact.name}_${artifact.namespace}_${collection.type.name}`
            .toLowerCase()
            .replace("@", "at__")
            .replace("/", "__");

        const existing = await repo.findOne({
          relations: {
            projects: true,
          },
          where: {
            slug: canonicalSlug,
          },
        });

        if (existing) {
          logger.debug(`removing existing ${canonicalSlug}`);
          // delete relations
          await repo
            .createQueryBuilder()
            .relation(Collection, "projects")
            .of(existing.id)
            .remove(existing.projects);
          // delete the collection

          await repo.delete({
            id: existing.id,
          });
        }
        logger.debug(
          `renaming temporary collection[slug=${collection.slug}] to be ${canonicalSlug}`,
        );

        const namePrefix =
          collection.type.name === "ARTIFACT_DEPENDENTS"
            ? "Dependents of"
            : "Dependencies for";
        const name = `${namePrefix} ${artifact.name}`;

        // Rename the current one to the canonical slug
        await repo.update(
          {
            id: collection.id,
          },
          {
            name: name,
            slug: canonicalSlug,
          },
        );
      });
    }
  }

  async resolveDepToProjects(dep: Artifact) {
    if (Object.keys(this.artifactNameToProjectsMap).length === 0) {
      const allRelatedProjects = await this.projectRepository.find({
        relations: {
          artifacts: true,
        },
        where: {
          artifacts: {
            id: In(this.packages.map((p) => p.id)),
          },
        },
      });
      // Build the mapping
      this.artifactNameToProjectsMap = allRelatedProjects.reduce<
        Record<string, UniqueArray<Project>>
      >((acc, p) => {
        p.artifacts.forEach((a) => {
          const arr = acc[a.name] || new UniqueArray((p) => p.id);
          arr.push(p);
          acc[a.name] = arr;
        });
        return acc;
      }, {});
    }
    return this.artifactNameToProjectsMap[dep.name];
  }

  async writeBatch() {
    logger.debug("writing a batch of dependencies");
    const toWrite = this.batch;
    this.batch = [];

    // Retrieve collection types if they haven't already been retrieved
    if (Object.keys(this.collectionTypes).length === 0) {
      // Get the collection types
      const types = await this.collectionTypeRepository.find({
        where: {
          name: In(["ARTIFACT_DEPENDENTS", "ARTIFACT_DEPENDENCIES"]),
        },
      });
      if (types.length !== 2) {
        throw new Error("required collection types do not exist");
      }
      this.collectionTypes = _.keyBy(types, "name");
    }

    const writeQueue: Record<string, CollectionQueueStorage> = {};

    for (const row of toWrite) {
      const dependency = this.packageMap[row.package_name];
      const dependent = this.packageMap[row.dependent_name];
      // Skip if the dependent or dependency doesn't exist (that shouldn't
      // happen based on the query used)
      if (!dependency || !dependent) {
        logger.warn(
          "response from bigquery contained an unknown dependency or dependent",
        );
        logger.debug(row);
        continue;
      }

      const dependentsCollectionQueueStorage =
        await this.getTemporaryDependentsCollection(dependency);
      const dependenciesCollectionQueueStorage =
        await this.getTemporaryDependenciesCollection(dependent);

      const dependentsProjects = await this.resolveDepToProjects(dependent);
      const dependencysProjects = await this.resolveDepToProjects(dependency);

      dependencysProjects.items().forEach((dp) => {
        dependenciesCollectionQueueStorage.relations.push(dp);
      });

      dependentsProjects.items().forEach((dp) => {
        dependentsCollectionQueueStorage.relations.push(dp);
      });

      writeQueue[dependenciesCollectionQueueStorage.name] =
        dependenciesCollectionQueueStorage;
      writeQueue[dependentsCollectionQueueStorage.name] =
        dependentsCollectionQueueStorage;
    }

    for (const name in writeQueue) {
      // Clear queue storage
      const queueStorage = writeQueue[name];
      const queuedProjects = queueStorage.relations.items();

      const collection = await this.collectionRepository.findOneOrFail({
        relations: {
          projects: true,
        },
        where: {
          id: queueStorage.collection.id,
        },
      });

      const newProjects = _.differenceBy(
        queuedProjects,
        collection.projects,
        "id",
      );

      await this.collectionRepository
        .createQueryBuilder()
        .relation(Collection, "projects")
        .of(queueStorage.collection.id)
        .add(newProjects);
    }
  }

  async getTemporaryCollection(
    dep: Artifact,
    typeName: "ARTIFACT_DEPENDENTS" | "ARTIFACT_DEPENDENCIES",
  ) {
    const type = this.collectionTypes[typeName];
    const key = `${dep.name}:${typeName}`;
    let collectionQueue = this.tempCollectionQueue[key];
    if (!collectionQueue) {
      // Create the collection
      const tempName = `temp-${this.uuid}-${dep.name}-${typeName}`;
      const collection = Collection.create({
        name: tempName,
        slug: tempName,
        type: type,
        artifactOwner: dep,
      });
      await this.collectionRepository.insert(collection);
      collectionQueue = {
        name: tempName,
        collection: collection,
        relations: new UniqueArray((p) => p.id),
      };
      this.tempCollectionQueue[key] = collectionQueue;
    }
    return collectionQueue;
  }

  getTemporaryDependentsCollection(dep: Artifact) {
    return this.getTemporaryCollection(dep, "ARTIFACT_DEPENDENTS");
  }

  getTemporaryDependenciesCollection(dep: Artifact) {
    return this.getTemporaryCollection(dep, "ARTIFACT_DEPENDENCIES");
  }
}

export interface DependentsPeriodicCollectorOptions {
  depedentsTableId?: string;
}

export class DependentsPeriodicCollector implements IPeriodicCollector {
  private artifactRepository: Repository<Artifact>;
  private collectionRepository: Repository<Collection>;
  private collectionTypeRepository: Repository<CollectionType>;
  private projectRepository: Repository<Project>;
  private bq: BigQuery;
  private datasetId: string;
  private options: DependentsPeriodicCollectorOptions;

  constructor(
    artifactRepository: Repository<Artifact>,
    collectionRepository: Repository<Collection>,
    collectionTypeRepository: Repository<CollectionType>,
    projectRepository: Repository<Project>,
    bq: BigQuery,
    datasetId: string,
    options?: DependentsPeriodicCollectorOptions,
  ) {
    this.artifactRepository = artifactRepository;
    this.collectionRepository = collectionRepository;
    this.collectionTypeRepository = collectionTypeRepository;
    this.projectRepository = projectRepository;
    this.datasetId = datasetId;
    this.bq = bq;
    this.options = _.merge({}, options);
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
            new DependentsRecorder(
              npmPackages,
              this.collectionRepository,
              this.collectionTypeRepository,
              this.projectRepository,
              20000,
            ),
          )
          .on("close", () => {
            logger.debug("completed dependent/dependency collection");
            resolve();
          })
          .on("error", (err) => {
            logger.debug("caught an error reading/writing from the stream");
            reject(err);
          });
      });
    } catch (err) {
      logger.error(`caught error collecting dependencies`, JSON.stringify(err));
      throw err;
    }
  }

  private async getOrCreateDependentsTable(packages: Artifact[]) {
    if (this.options.depedentsTableId) {
      logger.debug("using supplied table id");
      const dataset = await this.ensureDataset();
      return dataset.table(this.options.depedentsTableId);
    }

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
