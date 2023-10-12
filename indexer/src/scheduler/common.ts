import { FindOptionsWhere, Repository } from "typeorm";
import { Artifact, Project } from "../db/orm-entities.js";
import { Range } from "../utils/ranges.js";
import {
  CollectResponse,
  IArtifactGroupCommitmentProducer,
  IArtifactGroup,
  ICollector,
} from "./types.js";
import { TimeSeriesCacheWrapper } from "../cacher/time-series.js";
import { IEventRecorder } from "../recorder/types.js";

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

export abstract class BaseCollector<T extends object> implements ICollector {
  async allArtifacts(): Promise<Artifact[]> {
    // By default this will simply iterate through the grouped artifacts
    const all: Artifact[] = [];
    for await (const artifacts of this.groupedArtifacts()) {
      all.push(...(await artifacts.artifacts()));
    }
    return all;
  }

  /* eslint-disable-next-line require-yield */
  async *groupedArtifacts(): AsyncGenerator<IArtifactGroup<T>> {
    throw new Error("groupedArtifacts() not implemented");
  }

  collect(
    _group: IArtifactGroup<T>,
    _range: Range,
    _committer: IArtifactGroupCommitmentProducer,
  ): Promise<CollectResponse> {
    throw new Error("groupedArtifacts() not implemented");
  }
}

export class ProjectArtifactsCollector extends BaseCollector<Project> {
  protected projectRepository: Repository<Project>;
  protected cache: TimeSeriesCacheWrapper;
  protected recorder: IEventRecorder;
  protected artifactsWhere: FindOptionsWhere<Artifact>;

  constructor(
    projectRepository: Repository<Project>,
    recorder: IEventRecorder,
    cache: TimeSeriesCacheWrapper,
    artifactsWhere: FindOptionsWhere<Artifact>,
  ) {
    super();
    this.projectRepository = projectRepository;
    this.cache = cache;
    this.recorder = recorder;
    this.artifactsWhere = artifactsWhere;
  }

  async *groupedArtifacts(): AsyncGenerator<IArtifactGroup<Project>> {
    const projects = await this.projectRepository.find({
      relations: {
        artifacts: true,
      },
      where: {
        artifacts: this.artifactsWhere,
      },
    });

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
    throw new Error("Not implemented");
  }
}
