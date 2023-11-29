import { In, Repository } from "typeorm";
import { CollectResponse, IPeriodicCollector } from "../scheduler/types.js";
import { Artifact, ArtifactType, Collection } from "../index.js";
import { BigQuery, Dataset, Table } from "@google-cloud/bigquery";
import { Storage } from "@google-cloud/storage";
import { sha1FromArray } from "../utils/source-ids.js";
import { logger } from "../utils/logger.js";
import { TransformCallback, TransformOptions, Writable } from "stream";
import { randomUUID } from "crypto";
import {
  ArtifactNamespace,
  CollectionType,
  Project,
  RepoDependency,
} from "../db/orm-entities.js";
import _ from "lodash";
import stream from "stream";
import { UniqueArray, asyncBatch } from "../utils/array.js";
import { GithubBaseMixin } from "./github/common.js";
import { MultiplexGithubGraphQLRequester } from "./github/multiplex-graphql.js";
import { IEventPointerManager } from "../scheduler/pointers.js";
import { DateTime } from "luxon";

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

function repositoryDependencies() {
  return {
    dependencyGraphManifests: {
      totalCount: true,
      nodes: {
        filename: true,
      },
      edges: {
        node: {
          blobPath: true,
          parseable: true,
          filename: true,
          dependencies: {
            totalCount: true,
            nodes: {
              packageName: true,
              requirements: true,
              hasDependencies: true,
              packageManager: true,
            },
          },
        },
      },
    },
  };
}

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
  private repoDeps: Record<number, UniqueArray<Project>>;
  private count: number;

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
    this.repoDeps = {};
    this.count = 0;
  }

  _write(
    row: DependentRawRow,
    _encoding: BufferEncoding,
    done: TransformCallback,
  ): void {
    logger.debug(
      `[DEPS: ${this.count++}] ${row.package_name} -> ${row.dependent_name}`,
    );
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

  async getProjectsForRepos(dependency: Artifact) {
    let repos = this.repoDeps[dependency.id];
    if (!repos) {
      const projectsForRepos = await this.projectRepository.find({
        where: {
          packageDependencies: {
            dependencyId: dependency.id,
          },
        },
      });
      const uniq = new UniqueArray<Project>((p) => p.id);
      projectsForRepos.forEach((p) => uniq.push(p));
      this.repoDeps[dependency.id] = uniq;
      repos = uniq;
    }
    return repos.items();
  }

  async resolveDepToProjects(dep: Artifact) {
    logger.debug(`resolving to project ${dep.name}`);
    console.log(dep.name);
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
    let map = this.artifactNameToProjectsMap[dep.name];
    if (!map) {
      this.artifactNameToProjectsMap[dep.name] = new UniqueArray<Project>(
        (p) => p.id,
      );
      map = this.artifactNameToProjectsMap[dep.name];
    }
    return map;
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
      // Skip if the dependent or dependency doesn't exist (we are ignoring those values)
      if (!dependency || !dependent) {
        continue;
      }

      const dependentsCollectionQueueStorage =
        await this.getTemporaryDependentsCollection(dependency);
      const dependenciesCollectionQueueStorage =
        await this.getTemporaryDependenciesCollection(dependent);

      const dependentsProjects = await this.resolveDepToProjects(dependent);

      // If the dependency appears in the repo dependency then we have an
      // artifact that is used by something that _might_ not be a package.
      // resolve all those projects and add them to dependentsProjects
      const additionalDependentProjects = await this.getProjectsForRepos(
        dependency,
      );

      const dependencysProjects = await this.resolveDepToProjects(dependency);

      dependencysProjects.items().forEach((dp) => {
        dependenciesCollectionQueueStorage.relations.push(dp);
      });

      dependentsProjects.items().forEach((dp) => {
        dependentsCollectionQueueStorage.relations.push(dp);
      });

      additionalDependentProjects.forEach((p) => {
        dependentsCollectionQueueStorage.relations.push(p);
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
  dependentsTableId?: string;
}

type Repo = {
  owner: string;
  name: string;
};

type DependencyResponse = {
  dependencyGraphManifests: {
    totalCount: number;
    nodes: Array<{
      filename: true;
    }>;
    edges: Array<{
      node: {
        blobPath: string;
        parseable: boolean;
        filename: string;
        dependencies: {
          totalCount: number;
          nodes: Array<{
            packageName: string;
            requirements: string;
            hasDependencies: boolean;
            packageManager: string;
          }>;
        };
      };
    }>;
  };
};

export class DependentsPeriodicCollector
  extends GithubBaseMixin
  implements IPeriodicCollector
{
  private artifactRepository: Repository<Artifact>;
  private collectionRepository: Repository<Collection>;
  private collectionTypeRepository: Repository<CollectionType>;
  private projectRepository: Repository<Project>;
  private repoDepsRepository: Repository<RepoDependency>;
  private bq: BigQuery;
  private gcs: Storage;
  private gcsBucket: string;
  private datasetId: string;
  private options: DependentsPeriodicCollectorOptions;
  private eventPointerManager: IEventPointerManager;

  constructor(
    eventPointerManager: IEventPointerManager,
    repoDepsRepository: Repository<RepoDependency>,
    artifactRepository: Repository<Artifact>,
    collectionRepository: Repository<Collection>,
    collectionTypeRepository: Repository<CollectionType>,
    projectRepository: Repository<Project>,
    bq: BigQuery,
    datasetId: string,
    gcs: Storage,
    gcsBucket: string,
    options?: DependentsPeriodicCollectorOptions,
  ) {
    super();
    this.eventPointerManager = eventPointerManager;
    this.repoDepsRepository = repoDepsRepository;
    this.artifactRepository = artifactRepository;
    this.collectionRepository = collectionRepository;
    this.collectionTypeRepository = collectionTypeRepository;
    this.projectRepository = projectRepository;
    this.datasetId = datasetId;
    this.bq = bq;
    this.gcs = gcs;
    this.gcsBucket = gcsBucket;
    this.options = _.merge({}, options);
  }

  async ensureDataset() {
    const ds = this.bq.dataset(this.datasetId);

    try {
      if (!(await ds.exists())) {
        throw new Error(
          `dataset ${this.datasetId} does not exist. please create it`,
        );
      }
    } catch (err) {
      throw new Error(
        `dataset ${this.datasetId} does not exist. please create it`,
      );
    }
    return ds;
  }

  private async getManyRepositoryDeps(locators: Repo[]) {
    const multiplex = new MultiplexGithubGraphQLRequester<
      Repo,
      DependencyResponse
    >(
      "getManyRepositories",
      {
        owner: "String!",
        name: "String!",
      },
      (vars) => {
        return {
          type: "repository",
          definition: {
            __args: {
              owner: vars.owner,
              name: vars.name,
            },
            ...repositoryDependencies(),
          },
        };
      },
    );
    return await this.rateLimitedGraphQLGeneratedRequest(multiplex, locators);
  }

  private async refreshDependenciesForAllRepositories() {
    // We are going to abuse the event pointers to implement a TTL for pulling dependency data.

    const artifacts = await this.artifactRepository.find({
      where: {
        type: ArtifactType.GIT_REPOSITORY,
        namespace: ArtifactNamespace.GITHUB,
      },
    });

    const validArtifacts = artifacts.filter((a) => {
      try {
        this.splitGithubRepoIntoLocator(a);
        return true;
      } catch (_e) {
        return false;
      }
    });

    const today = DateTime.now().toUTC().startOf("day");
    const tomorrow = today.plus({ day: 1 });
    const todayRange = {
      startDate: today,
      endDate: tomorrow,
    };
    const ttlRange = {
      startDate: today,
      endDate: today.plus({ day: 30 }),
    };
    const collectorName = "dependents";
    const missingArtifacts =
      await this.eventPointerManager.missingArtifactsForRange(
        collectorName,
        todayRange,
        validArtifacts,
      );

    let count = 0;
    // GH doesn't like double digit batched requests it seems.
    await asyncBatch(missingArtifacts, 8, async (batch) => {
      const locators = batch.map((a) => {
        const parsed = this.splitGithubRepoIntoLocator(a);
        return {
          owner: parsed.owner,
          name: parsed.repo,
        };
      });
      const res = await this.getManyRepositoryDeps(locators);
      for (let i = 0; i < res.items.length; i++) {
        const artifact = batch[i];
        const deps = res.items[i];
        if (!deps) {
          count += 1;
          await this.eventPointerManager.commitArtifactForRange(
            collectorName,
            ttlRange,
            artifact,
          );
          continue;
        }

        const npmArtifacts = deps.dependencyGraphManifests.edges.flatMap(
          (manifest) => {
            // One day we can remove the filter for now. Let's keep it.
            return manifest.node.dependencies.nodes
              .filter((d) => d.packageManager === "NPM")
              .map((dep) => {
                return {
                  name: dep.packageName.toLowerCase(),
                  namespace: ArtifactNamespace.NPM_REGISTRY,
                  type: ArtifactType.NPM_PACKAGE,
                };
              });
          },
        );

        const uniqNpmArtifacts = _.uniqBy(npmArtifacts, "name");

        logger.debug(`upserting ${npmArtifacts.length} npm artifacts`);
        await this.artifactRepository.upsert(uniqNpmArtifacts, {
          conflictPaths: ["namespace", "name"],
          upsertType: "on-conflict-do-update",
        });

        const allDeps = await this.artifactRepository.find({
          where: {
            name: In(uniqNpmArtifacts.map((a) => a.name)),
            namespace: ArtifactNamespace.NPM_REGISTRY,
            type: ArtifactType.NPM_PACKAGE,
          },
        });

        const repoDeps = allDeps.map((a) => {
          return {
            repo: artifact,
            dependency: a,
          };
        });

        logger.debug(`updating all ${repoDeps.length} repository dependencies`);
        await this.repoDepsRepository.manager.transaction(async (manager) => {
          const repo = manager.withRepository(this.repoDepsRepository);

          // Delete all of the deps for this artifact
          await repo.delete({
            repo: {
              id: artifact.id,
            },
          });

          // Add new ones
          await repo.insert(repoDeps);
        });

        await this.eventPointerManager.commitArtifactForRange(
          collectorName,
          ttlRange,
          artifact,
        );
        count += 1;
      }
      logger.debug(
        `completed dependency collection [${count}/${missingArtifacts.length}]`,
      );
    });
    throw new Error("test");
  }

  async collect(): Promise<CollectResponse> {
    logger.debug("collecting dependents for all npm packages");

    await this.refreshDependenciesForAllRepositories();

    // Get a list of all `NPM_PACKAGES` in our database
    const npmPackages = await this.artifactRepository.find({
      where: {
        type: ArtifactType.NPM_PACKAGE,
      },
      order: {
        id: { direction: "ASC" },
      },
    });

    logger.debug(`found ${npmPackages.length} npm packages`);

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
              1000000,
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
    if (this.options.dependentsTableId) {
      logger.debug("using supplied table id");
      const dataset = await this.ensureDataset();
      return dataset.table(this.options.dependentsTableId);
    }

    const packagesSha1 = sha1FromArray(
      packages.map((a) => {
        return `${a.id},${a.name}`;
      }),
    );

    // Check if the dataset's table already exists
    const tableId = `npm_dependents_${packagesSha1}`;

    logger.debug(`checking for table ${tableId}`);

    const dataset = await this.ensureDataset();
    const destinationTable = dataset.table(tableId);

    const [destinationTableExists] = await destinationTable.exists();
    if (destinationTableExists) {
      logger.debug("table exists. no need to query BQ");
      return destinationTable;
    }

    await this.queryWithPackages(
      dataset,
      packagesSha1,
      packages,
      destinationTable,
    );

    return destinationTable;
  }

  private async ensurePackageTable(
    dataset: Dataset,
    packagesSha1: string,
    packages: Artifact[],
  ) {
    logger.debug(`ensuring the package table exists`);
    const bucket = this.gcs.bucket(this.gcsBucket);
    const tableId = `oso_npm_packages_${packagesSha1}`;
    const file = bucket.file(`${tableId}.csv`);

    const passThroughStream = new stream.PassThrough();
    passThroughStream.write("id,package_name\n");
    packages.forEach((p) => passThroughStream.write(`${p.id},${p.name}\n`));
    passThroughStream.end();

    await new Promise<void>((resolve, reject) => {
      passThroughStream
        .pipe(file.createWriteStream())
        .on("finish", () => {
          resolve();
        })
        .on("error", (err) => {
          reject(err);
        });
    });

    // Create a BQ table with the newly uploaded .csv
    const uploadMeta = {
      sourceFormat: "CSV",
      skipLeadingRows: 1,
      schema: {
        fields: [
          { name: "id", type: "INT64" },
          { name: "package_name", type: "STRING" },
        ],
      },
      location: "US",
    };
    const table = dataset.table(tableId);
    const [job] = await table.load(file, uploadMeta);
    const errors = job.status?.errors;
    if (errors && errors.length > 0) {
      logger.debug(`failed to upload table to ${tableId} on job ${job.id}`);
      throw errors;
    }
    const [metadata] = await table.getMetadata();
    console.log(metadata);
    logger.debug(
      `uploaded table to ${tableId} on job ${job.id} ${table.projectId}.${table.dataset.id}.${table.id}`,
    );
    return `${metadata.tableReference.projectId}.${table.dataset.id}.${table.id}`;
  }

  private async queryWithPackages(
    dataset: Dataset,
    packagesSha1: string,
    packages: Artifact[],
    destinationTable: Table,
  ) {
    const packageTableName = await this.ensurePackageTable(
      dataset,
      packagesSha1,
      packages,
    );

    // Query the bigquery public dataset into a temporary table
    //
    // TODO: For now this is hardcoded to the snapshot of deps from 2023-10-16
    // to reduce the number of results to scan on BQ
    const query = `
			SELECT 
				Name as package_name, 
				Dependent.Name as dependent_name,
				MIN(MinimumDepth) as minimum_depth
			FROM 
				\`bigquery-public-data.deps_dev_v1.Dependents\` AS d
      INNER JOIN \`${packageTableName}\` AS pp
        ON Lower(pp.package_name) = Lower(d.Name)
      INNER JOIN \`${packageTableName}\` as pd
        ON Lower(pd.package_name) = Lower(d.Dependent.Name)
			WHERE 
				TIMESTAMP_TRUNC(SnapshotAt, DAY) = TIMESTAMP('2023-10-16')
				AND System = 'NPM'
				AND MinimumDepth < 4
      GROUP BY 1,2
		`;

    const options = {
      query: query,
      location: "US",
      destination: destinationTable,
    };
    const [job] = await this.bq.createQueryJob(options);
    // Wait for the job to complete
    await job.getQueryResults({ maxResults: 0 });
    logger.debug(`biqquery job complete`);
  }
}
