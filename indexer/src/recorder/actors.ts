import { Artifact, ArtifactNamespace } from "../db/orm-entities.js";
import {
  IActorDirectory,
  IncompleteArtifact,
  IncompleteActor,
  UnknownActor,
} from "./types.js";

type IdType = string | number;

export class ActorLookup<
  I extends IdType,
  V extends IncompleteActor<N, M> & { id: I },
  N extends string,
  M extends ArtifactNamespace,
> {
  private incompleteLookup: Record<M, Record<N, V>>;
  private idLookup: Record<I, V>;

  constructor() {
    this.incompleteLookup = {} as Record<M, Record<N, V>>;
    this.idLookup = {} as Record<I, V>;
  }

  add(item: V) {
    const namespaceLookup = this.getNamespaceLookup(item.namespace);
    namespaceLookup[item.name] = item;

    this.idLookup[item.id] = item;
  }

  private getNamespaceLookup(namespace: M) {
    let namespaceLookup = this.incompleteLookup[namespace];
    if (!namespaceLookup) {
      this.incompleteLookup[namespace] = {} as Record<N, V>;
      namespaceLookup = this.incompleteLookup[namespace];
    }
    return namespaceLookup;
  }

  byString(item: IncompleteActor<N, M>): V {
    return this.getNamespaceLookup(item.namespace)[item.name];
  }

  byId(id: I): V {
    return this.idLookup[id];
  }

  knownSetOf(actors: IncompleteActor<N, M>[]): V[] {
    const known: V[] = [];
    actors.forEach((actor) => {
      const resolved = this.byString(actor);
      if (resolved) {
        known.push(resolved);
      }
    });
    return known;
  }

  unknownSetOf<T extends IncompleteActor<N, M>>(actors: T[]): T[] {
    return actors.filter((actor) => {
      return !this.byString(actor);
    });
  }
}

export class InmemActorResolver implements IActorDirectory {
  private artifactsLookup: ActorLookup<
    number,
    Artifact,
    string,
    ArtifactNamespace
  >;

  constructor() {
    this.artifactsLookup = new ActorLookup();
  }

  async fromId(id: number): Promise<Artifact> {
    return this.artifactsLookup.byId(id);
  }

  async resolveArtifactId(artifact: IncompleteArtifact): Promise<number> {
    const resolved = this.artifactsLookup.byString(artifact);
    if (!resolved) {
      throw new UnknownActor(
        `Artifact unknown name=${artifact.name} namespace=${artifact.namespace}`,
      );
    }
    return resolved.id;
  }

  loadArtifact(artifact: Artifact) {
    this.artifactsLookup.add(artifact);
  }

  knownArtifactsFrom(artifacts: IncompleteArtifact[]): Artifact[] {
    return this.artifactsLookup.knownSetOf(artifacts);
  }

  unknownArtifactsFrom(artifacts: IncompleteArtifact[]): IncompleteArtifact[] {
    return this.artifactsLookup.unknownSetOf(artifacts);
  }
}
