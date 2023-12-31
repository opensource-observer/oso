import { FindOptionsWhere, Repository } from "typeorm";
import { Artifact, Project } from "../db/orm-entities.js";
import { Range } from "../utils/ranges.js";
import {
  CollectResponse,
  IArtifactGroupCommitmentProducer,
  IArtifactGroup,
  IEventCollector,
} from "./types.js";
import { TimeSeriesCacheWrapper } from "../cacher/time-series.js";
import { IEventRecorderClient } from "../recorder/types.js";

export class BasicArtifactGroup<T extends object> implements IArtifactGroup<T> {
  private _name: string;
  private _meta: T;
  private _artifacts: Artifact[];

  constructor(name: string, meta: T, artifacts: Artifact[]) {
    this._name = name;
    this._meta = meta;
    this._artifacts = artifacts;
  }

  async name() {
    return this._name;
  }

  async meta() {
    return this._meta;
  }

  async artifacts() {
    return this._artifacts;
  }

  async createMissingGroup(missing: Artifact[]): Promise<IArtifactGroup<T>> {
    return new BasicArtifactGroup(this._name, this._meta, missing);
  }
}

export class ProjectArtifactGroup extends BasicArtifactGroup<Project> {
  static create(project: Project, artifacts: Artifact[]) {
    return new ProjectArtifactGroup(
      `Project[slug=${project.slug}]`,
      project,
      artifacts,
    );
  }
}

export abstract class BaseEventCollector<T extends object>
  implements IEventCollector
{
  async allArtifacts(): Promise<Artifact[]> {
    throw new Error(
      "#allArtifacts not implemented for a base collector artifact",
    );
  }

  /* eslint-disable-next-line require-yield */
  async *groupedArtifacts(): AsyncGenerator<IArtifactGroup<T>> {
    throw new Error("#groupedArtifacts() not implemented");
  }

  collect(
    _group: IArtifactGroup<T>,
    _range: Range,
    _committer: IArtifactGroupCommitmentProducer,
  ): Promise<CollectResponse> {
    throw new Error("#collect not implemented");
  }
}

export class ProjectArtifactsCollector extends BaseEventCollector<Project> {
  protected projectRepository: Repository<Project>;
  protected cache: TimeSeriesCacheWrapper;
  protected recorder: IEventRecorderClient;
  protected artifactsWhere: FindOptionsWhere<Artifact>;

  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorderClient,
    cache: TimeSeriesCacheWrapper,
    artifactsWhere: FindOptionsWhere<Artifact>,
  ) {
    super();
    this.projectRepository = projectRepository;
    this.cache = cache;
    this.recorder = recorder;
    this.artifactsWhere = artifactsWhere;
  }

  async allArtifacts(): Promise<Artifact[]> {
    const projects = await this.allProjectsWithArtifacts();
    const uniqueIds: Record<number, boolean> = {};
    return projects.reduce<Artifact[]>((artifacts, p) => {
      p.artifacts.forEach((a) => {
        if (uniqueIds[a.id]) {
          return;
        }
        uniqueIds[a.id] = true;
        artifacts.push(a);
      });
      return artifacts;
    }, []);
  }

  protected async allProjectsWithArtifacts(): Promise<Project[]> {
    return await this.projectRepository.find({
      relations: {
        artifacts: true,
      },
      where: {
        artifacts: this.artifactsWhere,
      },
    });
  }

  async *groupedArtifacts(): AsyncGenerator<IArtifactGroup<Project>> {
    const projects = await this.allProjectsWithArtifacts();

    // Emit each project's artifacts as a group of artifacts to record
    for (const project of projects) {
      yield ProjectArtifactGroup.create(project, project.artifacts);
    }
  }

  collect(
    _group: IArtifactGroup<Project>,
    _range: Range,
    _committer: IArtifactGroupCommitmentProducer,
  ): Promise<CollectResponse> {
    throw new Error("#collect Not implemented");
  }
}

export type Batch = {
  size: number;
  name: string;
  totalBatches: number;
};

export class BatchArtifactsCollector extends BaseEventCollector<Batch> {
  protected cache: TimeSeriesCacheWrapper;
  protected recorder: IEventRecorderClient;
  protected batchSize: number;

  constructor(
    recorder: IEventRecorderClient,
    cache: TimeSeriesCacheWrapper,
    batchSize: number,
  ) {
    super();
    this.cache = cache;
    this.recorder = recorder;
    this.batchSize = batchSize;
  }

  async allArtifacts(): Promise<Artifact[]> {
    throw new Error("#allArtifacts not implemented for a batch artifact");
  }

  async *groupedArtifacts(): AsyncGenerator<IArtifactGroup<Batch>> {
    const allUnsorted = await this.allArtifacts();
    const all = allUnsorted.sort((a, b) => {
      return a.id - b.id;
    });

    let batchNumber = 0;
    const batches = Math.ceil(all.length / this.batchSize);
    // Emit each project's artifacts as a group of artifacts to record
    for (let i = 0; i < all.length; i += this.batchSize) {
      batchNumber += 1;
      const batchArtifacts = all.slice(i, i + this.batchSize);
      const batchName = `Batch[${batchNumber}/${batches}]`;
      const batch: Batch = {
        totalBatches: batches,
        size: batchArtifacts.length,
        name: batchName,
      };

      yield new BasicArtifactGroup(batchName, batch, batchArtifacts);
    }
  }

  collect(
    _group: IArtifactGroup<Batch>,
    _range: Range,
    _committer: IArtifactGroupCommitmentProducer,
  ): Promise<CollectResponse> {
    throw new Error("Not implemented");
  }
}

export class BatchedProjectArtifactsCollector extends BatchArtifactsCollector {
  protected projectRepository: Repository<Project>;
  protected artifactsWhere: FindOptionsWhere<Artifact>;

  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorderClient,
    cache: TimeSeriesCacheWrapper,
    batchSize: number,
    artifactsWhere: FindOptionsWhere<Artifact>,
  ) {
    super(recorder, cache, batchSize);
    this.projectRepository = projectRepository;
    this.artifactsWhere = artifactsWhere;
    this.cache = cache;
    this.recorder = recorder;
  }

  async allArtifacts(): Promise<Artifact[]> {
    const projects = await this.allProjectsWithArtifacts();
    const uniqueIds: Record<number, boolean> = {};
    return projects.reduce<Artifact[]>((artifacts, p) => {
      p.artifacts.forEach((a) => {
        if (uniqueIds[a.id]) {
          return;
        }
        uniqueIds[a.id] = true;
        artifacts.push(a);
      });
      return artifacts;
    }, []);
  }

  protected async allProjectsWithArtifacts(): Promise<Project[]> {
    return await this.projectRepository.find({
      relations: {
        artifacts: true,
      },
      where: {
        artifacts: this.artifactsWhere,
      },
    });
  }
}
