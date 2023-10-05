import {
  BaseEntity,
  BeforeInsert,
  BeforeUpdate,
  Column,
  ViewColumn,
  Entity,
  ViewEntity,
  Index,
  JoinTable,
  ManyToMany,
  ManyToOne,
  OneToMany,
  PrimaryColumn,
  PrimaryGeneratedColumn,
  CreateDateColumn,
  UpdateDateColumn,
} from "typeorm";
import { IsUrl, IsOptional, validateOrReject } from "class-validator";
import type { Brand } from "utility-types";
import { normalizeToObject } from "../utils/common.js";

export enum EventType {
  FUNDING = "FUNDING",
  PULL_REQUEST_CREATED = "PULL_REQUEST_CREATED",
  PULL_REQUEST_MERGED = "PULL_REQUEST_MERGED",
  COMMIT_CODE = "COMMIT_CODE",
  ISSUE_FILED = "ISSUE_FILED",
  ISSUE_CLOSED = "ISSUE_CLOSED",
  DOWNSTREAM_DEPENDENCY_COUNT = "DOWNSTREAM_DEPENDENCY_COUNT",
  UPSTREAM_DEPENDENCY_COUNT = "UPSTREAM_DEPENDENCY_COUNT",
  DOWNLOADS = "DOWNLOADS",
  CONTRACT_INVOKED = "CONTRACT_INVOKED",
  USERS_INTERACTED = "USERS_INTERACTED",
  CONTRACT_INVOKED_AGGREGATE_STATS = "CONTRACT_INVOKED_AGGREGATE_STATS",
  PULL_REQUEST_CLOSED = "PULL_REQUEST_CLOSED",
  STAR_AGGREGATE_STATS = "STAR_AGGREGATE_STATS",
  PULL_REQUEST_REOPENED = "PULL_REQUEST_REOPENED",
  PULL_REQUEST_REMOVED_FROM_PROJECT = "PULL_REQUEST_REMOVED_FROM_PROJECT",
  PULL_REQUEST_APPROVED = "PULL_REQUEST_APPROVED",
  ISSUE_CREATED = "ISSUE_CREATED",
  ISSUE_REOPENED = "ISSUE_REOPENED",
  ISSUE_REMOVED_FROM_PROJECT = "ISSUE_REMOVED_FROM_PROJECT",
  STARRED = "STARRED",
  FORK_AGGREGATE_STATS = "FORK_AGGREGATE_STATS",
  FORKED = "FORKED",
  WATCHER_AGGREGATE_STATS = "WATCHER_AGGREGATE_STATS",
}

export enum ArtifactType {
  EOA_ADDRESS = "EOA_ADDRESS",
  SAFE_ADDRESS = "SAFE_ADDRESS",
  CONTRACT_ADDRESS = "CONTRACT_ADDRESS",
  FACTORY_ADDRESS = "FACTORY_ADDRESS",
  GIT_REPOSITORY = "GIT_REPOSITORY",
  GIT_EMAIL = "GIT_EMAIL",
  GIT_NAME = "GIT_NAME",
  GITHUB_ORG = "GITHUB_ORG",
  GITHUB_USER = "GITHUB_USER",
  NPM_PACKAGE = "NPM_PACKAGE",
}

export enum ArtifactNamespace {
  ETHEREUM = "ETHEREUM",
  OPTIMISM = "OPTIMISM",
  GOERLI = "GOERLI",
  GITHUB = "GITHUB",
  GITLAB = "GITLAB",
  NPM_REGISTRY = "NPM_REGISTRY",
}

export enum JobStatus {
  PENDING = "PENDING",
  COMPLETE = "COMPLETE",
  // Used to prevent a job from scheduling temporarily
  MANUALLY_LOCKED = "MANUALLY_LOCKED",
}

export enum JobExecutionStatus {
  ACTIVE = "ACTIVE",
  COMPLETE = "COMPLETE",
  FAILED = "FAILED",
}

abstract class Base<IdTag> extends BaseEntity {
  @PrimaryGeneratedColumn()
  id: Brand<number, IdTag>;

  @CreateDateColumn({ type: "timestamptz" })
  createdAt: Date;
  @UpdateDateColumn({ type: "timestamptz" })
  updatedAt: Date;
  @Column("timestamptz", { nullable: true })
  deletedAt: Date | null;

  toJSON() {
    return normalizeToObject(this);
  }

  @BeforeInsert()
  @BeforeUpdate()
  async validate() {
    await validateOrReject(this);
  }
}

@Entity()
export class Collection extends Base<"CollectionId"> {
  @Column("text")
  name: string;

  @Column("text", { nullable: true })
  @IsOptional()
  description: string | null;

  @Column("boolean", { default: false })
  verified: boolean;

  @Column("text", { unique: true })
  slug: string;

  @ManyToMany(() => Project, (project) => project.collections)
  @JoinTable()
  projects: Project[];
}

@Entity()
export class Project extends Base<"ProjectId"> {
  @Column("text")
  name: string;

  @Column("text", { nullable: true })
  @IsOptional()
  description: string | null;

  @Column("boolean", { default: false })
  verified: boolean;

  @Column("text", { unique: true })
  slug: string;

  @ManyToMany(() => Collection, (collection) => collection.projects)
  collections: Collection[];

  @ManyToMany(() => Artifact, (artifact) => artifact.projects)
  @JoinTable()
  artifacts: Artifact[];

  @OneToMany(() => EventsDailyByProject, (e) => e.project)
  eventsDailyByProject: EventsDailyByProject[];
}

@Entity()
@Index(["namespace", "name"], { unique: true })
export class Artifact extends Base<"ArtifactId"> {
  @Column("enum", { enum: ArtifactType })
  type: ArtifactType;

  @Column("enum", { enum: ArtifactNamespace })
  namespace: ArtifactNamespace;

  @Column("text")
  name: string;

  @Column("text", { nullable: true })
  @IsUrl()
  @IsOptional()
  url: string | null;

  @ManyToMany(() => Project, (project) => project.artifacts)
  projects: Project[];

  @OneToMany(() => Event, (event) => event.to)
  eventsAsTo: Event[];
  @OneToMany(() => Event, (event) => event.from)
  eventsAsFrom: Event[];
  @OneToMany(() => EventsDailyByArtifact, (e) => e.to)
  eventsDailyByArtifact: EventsDailyByArtifact[];

  @OneToMany(() => EventPointer, (eventPointer) => eventPointer.artifact)
  eventPointers: EventPointer[];
}

@Entity()
@Index(["time"])
@Index(["id", "time"], { unique: true })
@Index(["sourceId", "time"], { unique: true })
export class Event {
  @PrimaryColumn("integer", { generated: "increment" })
  id: Brand<number, "EventId">;

  @Column("text")
  sourceId: string;

  @Column("enum", { enum: EventType })
  type: EventType;

  @PrimaryColumn("timestamptz")
  time: Date;

  @ManyToOne(() => Artifact, (artifact) => artifact.eventsAsTo)
  to: Artifact;

  @ManyToOne(() => Artifact, (artifact) => artifact.eventsAsFrom, {
    nullable: true,
  })
  @IsOptional()
  from: Artifact | null;

  @Column("float")
  amount: number;
}

@Entity()
@Index(["artifact", "collector", "startDate", "endDate"], { unique: true })
export class EventPointer extends Base<"EventPointerId"> {
  @ManyToOne(() => Artifact, (artifact) => artifact.eventPointers)
  artifact: Artifact;

  @Column("text")
  collector: string;

  @Column("timestamptz")
  startDate: Date;

  @Column("timestamptz")
  endDate: Date;

  @Column("int")
  version: number;
}

@Entity()
@Index(["scheduledTime", "collector"], { unique: true })
export class Job extends Base<"JobId"> {
  @Column("text", { nullable: true })
  group: string | null;

  @Column("timestamptz")
  scheduledTime: Date;

  @Column("text")
  collector: string;

  @Column("enum", { enum: JobStatus })
  status: JobStatus;

  // Used to prevent concurrent writes to this object
  @Column("integer", {
    default: 0,
  })
  version: number;

  @Column("jsonb", {
    default: {},
  })
  options: Record<string, any>;

  @OneToMany(() => JobExecution, (jobExecution) => jobExecution.job)
  executions: JobExecution[];
}

@Entity()
@Index(["name"], { unique: true })
export class JobGroupLock extends Base<"JobGroupId"> {
  @Column("text")
  name: string;
}

@Entity()
@Index(["job", "attempt"], { unique: true })
export class JobExecution extends Base<"JobExecutionId"> {
  @Column("enum", { enum: JobExecutionStatus })
  status: JobExecutionStatus;

  @Column("integer")
  attempt: number;

  // Using the updatedAt field to maintain a row lock here doesn't seem to work
  // properly. Just using a simple counter.
  @Column("integer", { default: 0 })
  version: number;

  @ManyToOne(() => Job, (job) => job.executions)
  job: Job;

  @OneToMany(() => Log, (log) => log.execution)
  log: Log[];
}

@Entity()
export class Log extends Base<"LogId"> {
  @Column("text")
  level: string;

  @Column("jsonb")
  body: Record<string, any>;

  @ManyToOne(() => JobExecution, (jobExecution) => jobExecution.log)
  execution: JobExecution;
}

@ViewEntity({
  materialized: true,
  expression: `
    SELECT "toId",
      "type",
      time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
      SUM(amount) as "amount"
    FROM "event" 
    GROUP BY "toId", "type", "bucketDaily"
    WITH NO DATA;
  `,
})
export class EventsDailyByArtifact {
  @ManyToOne(() => Artifact, (artifact) => artifact.eventsDailyByArtifact)
  @ViewColumn()
  to: Artifact;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketDaily: Date;

  @ViewColumn()
  amount: number;
}

@ViewEntity({
  materialized: true,
  expression: `
    SELECT "projectId",
      "type",
      time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
      SUM(amount) as "amount"
    FROM "event"
    INNER JOIN "project_artifacts_artifact"
      on "project_artifacts_artifact"."artifactId" = "event"."toId"
    GROUP BY "projectId", "type", "bucketDaily"
    WITH NO DATA;
  `,
})
export class EventsDailyByProject {
  @ManyToOne(() => Project, (project) => project.eventsDailyByProject)
  @ViewColumn()
  project: Project;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketDaily: Date;

  @ViewColumn()
  amount: number;
}
