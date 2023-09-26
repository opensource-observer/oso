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
  FUNDING = "funding",
  PULL_REQUEST_CREATED = "pull_request_created",
  PULL_REQUEST_MERGED = "pull_request_merged",
  COMMIT_CODE = "commit_code",
  ISSUE_FILED = "issue_filed",
  ISSUE_CLOSED = "issue_closed",
  DOWNSTREAM_DEPENDENCY_COUNT = "downstream_dependency_count",
  UPSTREAM_DEPENDENCY_COUNT = "upstream_dependency_count",
  DOWNLOADS = "downloads",
  CONTRACT_INVOKED = "contract_invoked",
  USERS_INTERACTED = "users_interacted",
  CONTRACT_INVOKED_AGGREGATE_STATS = "contract_invoked_aggregate_stats",
  PULL_REQUEST_CLOSED = "pull_request_closed",
  STAR_AGGREGATE_STATS = "star_aggregate_stats",
  PULL_REQUEST_REOPENED = "pull_request_reopened",
  PULL_REQUEST_REMOVED_FROM_PROJECT = "pull_request_removed_from_project",
  PULL_REQUEST_APPROVED = "pull_request_approved",
  ISSUE_CREATED = "issue_created",
  ISSUE_REOPENED = "issue_reopened",
  ISSUE_REMOVED_FROM_PROJECT = "issue_removed_from_project",
  STARRED = "starred",
  FORK_AGGREGATE_STATS = "fork_aggregate_stats",
  FORKED = "forked",
  WATCHER_AGGREGATE_STATS = "watcher_aggregate_stats",
}

export enum ArtifactType {
  EOA_ADDRESS = "eoa_address",
  SAFE_ADDRESS = "safe_address",
  CONTRACT_ADDRESS = "contract_address",
  FACTORY_ADDRESS = "factory_address",
  GIT_REPOSITORY = "git_repository",
  GIT_EMAIL = "git_email",
  GIT_NAME = "git_name",
  GITHUB_ORG = "github_org",
  GITHUB_USER = "github_user",
  NPM_PACKAGE = "npm_package",
}

export enum ArtifactNamespace {
  ETHEREUM = "ethereum",
  OPTIMISM = "optimism",
  GOERLI = "goerli",
  GITHUB = "github",
  GITLAB = "gitlab",
  NPM_REGISTRY = "NPM_REGISTRY",
}

export enum JobStatus {
  PENDING = "pending",
  COMPLETE = "complete",
}

export enum JobExecutionStatus {
  ACTIVE = "active",
  COMPLETE = "complete",
  FAILED = "failed",
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
export class Job extends Base<"JobId"> {
  @Column("text")
  execGroup: string;

  @Column("timestamptz")
  scheduledTime: Date;

  @Column("text")
  collector: string;

  @Column("enum", { enum: JobStatus })
  status: JobStatus;

  @OneToMany(() => JobExecution, (jobExecution) => jobExecution.job)
  executions: JobExecution[];
}

@Entity()
export class JobExecution extends Base<"JobExecutionId"> {
  @Column("enum", { enum: JobExecutionStatus })
  status: JobExecutionStatus;

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
