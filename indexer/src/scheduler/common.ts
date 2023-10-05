import { Artifact, Project } from "../db/orm-entities.js";
import { IArtifactGroup } from "./types.js";

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
