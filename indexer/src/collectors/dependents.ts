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
import { Brand } from "utility-types";
import { DataSource } from "typeorm/browser";

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

type TempCollectionType = { artifactOwnerId: number; id: number };

class DependentsRecorder extends Writable {
  private collectionRepository: Repository<Collection>;
  private collectionTypeRepository: Repository<CollectionType>;
  private projectRepository: Repository<Project>;
  private batchSize: number;
  private batch: {
    packageNames: string[];
    dependentNames: string[];
    minimumDepths: number[];
  };
  private packages: Artifact[];
  private uuid: string;
  private packageMap: Record<string, Artifact>;
  private tempCollectionQueue: Record<string, CollectionQueueStorage>;
  private collectionTypes: Record<string, CollectionType>;
  private artifactNameToProjectsMap: Record<string, UniqueArray<Project>>;
  private repoDeps: Record<number, UniqueArray<Project>>;
  private count: number;
  private initialized: boolean;
  private dataSource: DataSource;

  constructor(
    packages: Artifact[],
    dataSource: DataSource,
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
    this.dataSource = dataSource;
    this.collectionRepository = collectionRepository;
    this.collectionTypeRepository = collectionTypeRepository;
    this.projectRepository = projectRepository;
    this.resetBatch();
    this.packages = packages;
    this.uuid = randomUUID();
    this.tempCollectionQueue = {};
    this.collectionTypes = {};
    this.artifactNameToProjectsMap = {};
    this.packageMap = _.keyBy(packages, "name");
    this.repoDeps = {};
    this.count = 0;
    this.initialized = false;
  }

  addRow(row: DependentRawRow) {
    this.batch.packageNames.push(row.package_name);
    this.batch.dependentNames.push(row.dependent_name);
    this.batch.minimumDepths.push(row.minimum_depth);
  }

  get batchLength() {
    return this.batch.packageNames.length;
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
      this.addRow(row);
    }

    if (this.batchLength < this.batchSize && row !== null) {
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
    this.writeBatch()
      .then(() => {
        return this.commitAll();
      })
      .then(() => {
        done();
      })
      .catch((err) => {
        done(err);
      });
  }

  async commitAll() {
    // Many of the things in this method would be much faster if we just added
    // the artifact/collection/project table to bigquery. For now, this is a
    // punt until we figure out the proper design for that architecture.

    // Start calculating the artifact ids
    await this.dataSource.query(`
      CREATE TABLE ${this.dependentsToArtifactTable} (
        package_artifact_id int,
        dependent_artifact_id int
      )
    `);

    logger.debug(`materialize deps as artifacts`);
    await this.dataSource.query(`
      INSERT INTO ${this.dependentsToArtifactTable} ("package_artifact_id", "dependent_artifact_id") 
      SELECT DISTINCT
        a_p.id AS package_artifact_id,
        a_d.id AS dependent_artifact_id
      FROM 
        ${this.importedTableName} d 
      INNER JOIN artifact a_p ON a_p."namespace" = 'NPM_REGISTRY' AND a_p."name" = d.dependent_name 
      INNER JOIN artifact a_d ON a_d."namespace" = 'NPM_REGISTRY' AND a_d."name" = d.package_name 
    `);

    logger.debug(
      `resolving from repo dependencies to higher order dependencies. this will take a while`,
    );
    await this.dataSource.query(`
      INSERT INTO ${this.dependentsToArtifactTable} ("package_artifact_id", "dependent_artifact_id")
      SELECT 
        dta.package_artifact_id as package_artifact_id,
        rd."repoId" as dependent_artifact_id
      FROM repo_dependency rd 
      INNER JOIN ${this.dependentsToArtifactTable} dta ON dta.dependent_artifact_id = rd."dependencyId" 
    `);

    logger.debug(`copy deps from repo_dependency table`);
    await this.dataSource.query(`
      INSERT INTO ${this.dependentsToArtifactTable} ("package_artifact_id", "dependent_artifact_id")
      SELECT
        rd."dependencyId" AS package_artifact_id,
        rd."repoId" AS dependent_artifact_id
      FROM repo_dependency rd 
    `);

    // Creating temporary collections
    logger.debug(`create dependent temp collections`);
    const convertTempCollectionTypeToDBInput = (
      input: TempCollectionType[],
    ) => {
      return input.reduce<{ artifactOwnerIds: number[]; ids: number[] }>(
        (a, c) => {
          a.artifactOwnerIds.push(c.artifactOwnerId);
          a.ids.push(c.id);
          return a;
        },
        { artifactOwnerIds: [], ids: [] },
      );
    };

    const dependenciesCollections = (await this.dataSource.query(
      `
      WITH distinct_dependents AS (
        SELECT DISTINCT 
          dtp.dependent_artifact_id AS dependent_artifact_id,
          a.id AS "name" 
        FROM ${this.dependentsToArtifactTable} dtp
        INNER JOIN artifact a ON dtp.dependent_artifact_id = a.id
      )
      INSERT INTO collection("name", "slug", "artifactOwnerId", "typeId")
      SELECT 
        FORMAT('temp-%s-%s-%s', $1::text, $2::text, dd."name"),
        FORMAT('temp-%s-%s-%s', $1::text, $2::text, dd."name"),
        dd.dependent_artifact_id,
        $3::int
      FROM distinct_dependents dd
      RETURNING "id", "artifactOwnerId"
    `,
      [
        this.uuid,
        // The naming of things is opposite of what it might seem. If it showing
        // up as a dependent in the DB that means it has dependencies. Hence this
        // being DEPENDENCIES
        "ARTIFACT_DEPENDENCIES",
        this.collectionTypes["ARTIFACT_DEPENDENCIES"].id,
      ],
    )) as TempCollectionType[];
    const dependenciesCollectionsDBInput = convertTempCollectionTypeToDBInput(
      dependenciesCollections,
    );

    logger.debug(`create dependencies temp collections`);
    const dependentsCollections = (await this.dataSource.query(
      `
      WITH distinct_dependencies AS (
        SELECT DISTINCT 
          dtp.package_artifact_id AS package_artifact_id,
          a.id AS "name" 
        FROM ${this.dependentsToArtifactTable} dtp
        INNER JOIN artifact a ON dtp.package_artifact_id = a.id
      )
      INSERT INTO collection("name", "slug", "artifactOwnerId", "typeId")
      SELECT 
        FORMAT('temp-%s-%s-%s', $1::text, $2::text, dd."name"),
        FORMAT('temp-%s-%s-%s', $1::text, $2::text, dd."name"),
        dd.package_artifact_id,
        $3::int
      FROM distinct_dependencies dd
      RETURNING "id", "artifactOwnerId"
    `,
      [
        this.uuid,
        // The naming of things is opposite of what it might seem. If it showing
        // up as a dependency in the DB that means it has dependents. Hence this
        // being DEPENDENTS
        "ARTIFACT_DEPENDENTS",
        this.collectionTypes["ARTIFACT_DEPENDENTS"].id,
      ],
    )) as { artifactOwnerId: number; id: number }[];
    const dependentsCollectionsDBInput = convertTempCollectionTypeToDBInput(
      dependentsCollections,
    );

    logger.debug("writing dependents to collections");
    await this.dataSource.query(
      `
      WITH dependents_to_projects AS (
        SELECT
          paa_p."projectId" as package_project_id,
          dta."package_artifact_id",
          paa_d."projectId" as dependent_project_id,
          dta."dependent_artifact_id"
        from ${this.dependentsToArtifactTable} dta
        inner join project_artifacts_artifact paa_p on paa_p."artifactId" = dta.package_artifact_id
        inner join project_artifacts_artifact paa_d on paa_d."artifactId" = dta.dependent_artifact_id
      ), dependent_collections AS (
        SELECT * FROM UNNEST(
          $1::int[],
          $2::int[]
        ) AS t(artifact_id, collection_id)
      ), insert_dependents AS (
        INSERT INTO collection_projects_project ("collectionId", "projectId")
        SELECT DISTINCT dc.collection_id, dtp.dependent_project_id 
        FROM dependent_collections dc
        INNER JOIN dependents_to_projects dtp ON dtp.package_artifact_id = dc.artifact_id
        RETURNING "collectionId", "projectId"
      )
      select count(*) from insert_dependents
    `,
      [
        dependentsCollectionsDBInput.artifactOwnerIds,
        dependentsCollectionsDBInput.ids,
      ],
    );

    logger.debug("writing dependencies to collections");
    await this.dataSource.query(
      `
      WITH dependents_to_projects AS (
        SELECT
          paa_p."projectId" as package_project_id,
          dta."package_artifact_id",
          paa_d."projectId" as dependent_project_id,
          dta."dependent_artifact_id"
        from ${this.dependentsToArtifactTable} dta
        inner join project_artifacts_artifact paa_p on paa_p."artifactId" = dta.package_artifact_id
        inner join project_artifacts_artifact paa_d on paa_d."artifactId" = dta.dependent_artifact_id
      ), dependency_collections AS (
        SELECT * FROM UNNEST(
          $1::int[],
          $2::int[]
        ) AS t(artifact_id, collection_id)
      ), insert_dependencies AS (
        INSERT INTO collection_projects_project ("collectionId", "projectId")
        SELECT DISTINCT dc.collection_id, dtp.package_project_id 
        FROM dependency_collections dc
        INNER JOIN dependents_to_projects dtp ON dtp.dependent_artifact_id = dc.artifact_id
        RETURNING "collectionId", "projectId"
      )
      select count(*) from insert_dependencies
    `,
      [
        dependenciesCollectionsDBInput.artifactOwnerIds,
        dependenciesCollectionsDBInput.ids,
      ],
    );

    // In a transaction delete the old collection if it exists and rename the current one
    await this.commitCollections(dependenciesCollections);
    await this.commitCollections(dependentsCollections);

    // Drop temp tables
    await this.dataSource.query(`
      DROP TABLE ${this.dependentsToArtifactTable}
    `);
    await this.dataSource.query(`
      DROP TABLE ${this.importedTableName}
    `);
  }

  async commitCollections(tempCollections: TempCollectionType[]) {
    for (const { id } of tempCollections) {
      const collection = await this.collectionRepository.findOneOrFail({
        relations: {
          artifactOwner: true,
          type: true,
        },
        where: {
          id: id as Brand<number, "CollectionId">,
        },
      });

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

  get importedTableName() {
    return `bq_npm_dependents_${this.uuid.replace(/-/g, "_")}`;
  }

  get dependentsToArtifactTable() {
    return `npm_dependents_as_artifacts_${this.uuid.replace(/-/g, "_")}`;
  }

  resetBatch() {
    this.batch = {
      packageNames: [],
      dependentNames: [],
      minimumDepths: [],
    };
  }

  async writeBatch() {
    logger.debug("writing a batch of dependencies");
    const toWrite = this.batch;
    this.resetBatch();

    if (!this.initialized) {
      await this.dataSource.query(`
        CREATE TABLE ${this.importedTableName} (
          package_name text,
          dependent_name text,
          minimum_depth smallint
        )
      `);
      this.initialized = true;
    }

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

    await this.dataSource.query(
      `
      INSERT INTO ${this.importedTableName} ("package_name", "dependent_name", "minimum_depth")
      SELECT * FROM unnest(
        $1::text[], $2::text[], $3::smallint[]
      )
    `,
      [toWrite.packageNames, toWrite.dependentNames, toWrite.minimumDepths],
    );
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
  private dataSource: DataSource;

  constructor(
    dataSource: DataSource,
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
    this.dataSource = dataSource;
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
              this.dataSource,
              this.collectionRepository,
              this.collectionTypeRepository,
              this.projectRepository,
              100000,
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
