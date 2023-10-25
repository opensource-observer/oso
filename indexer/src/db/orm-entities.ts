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
  JoinColumn,
} from "typeorm";
import { IsUrl, IsOptional, validateOrReject } from "class-validator";
import type { Brand } from "utility-types";
import { normalizeToObject } from "../utils/common.js";

/******************************
 * ENUMS
 ******************************/

export enum EventTypeEnum {
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

/******************************
 * TABLES
 ******************************/

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

// We need this to prevent circular references for Typeorm's relational mapping.
// This interface should only need to be internal to this file.
interface IArtifact {
  id: Brand<number, "ArtifactId">;
  type: ArtifactType;
  namespace: ArtifactNamespace;
  name: string;
  url: string | null;
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

  // Allow artifacts to own collections. These can be dependents or maybe some
  // other form of project relations.
  @ManyToOne("Artifact", "collections", {
    nullable: true,
  })
  @JoinColumn()
  @IsOptional()
  artifactOwner?: IArtifact;
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

  @OneToMany(() => EventsDailyToProject, (e) => e.project)
  eventsDailyToProject: EventsDailyToProject[];
  @OneToMany(() => EventsWeeklyToProject, (e) => e.project)
  eventsWeeklyToProject: EventsWeeklyToProject[];
  @OneToMany(() => EventsMonthlyToProject, (e) => e.project)
  eventsMonthlyToProject: EventsMonthlyToProject[];
  @OneToMany(() => EventsDailyFromProject, (e) => e.project)
  eventsDailyFromProject: EventsDailyFromProject[];
  @OneToMany(() => EventsWeeklyFromProject, (e) => e.project)
  eventsWeeklyFromProject: EventsWeeklyFromProject[];
  @OneToMany(() => EventsMonthlyFromProject, (e) => e.project)
  eventsMonthlyFromProject: EventsMonthlyFromProject[];
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

  @OneToMany(() => Collection, (collection) => collection.artifactOwner)
  collections: Collection[];

  @OneToMany(() => Event, (event) => event.to)
  eventsAsTo: Event[];
  @OneToMany(() => Event, (event) => event.from)
  eventsAsFrom: Event[];

  @OneToMany(() => EventsDailyToArtifact, (e) => e.artifact)
  eventsDailyToArtifact: EventsDailyToArtifact[];
  @OneToMany(() => EventsWeeklyToArtifact, (e) => e.artifact)
  eventsWeeklyToArtifact: EventsWeeklyToArtifact[];
  @OneToMany(() => EventsMonthlyToArtifact, (e) => e.artifact)
  eventsMonthlyToArtifact: EventsMonthlyToArtifact[];
  @OneToMany(() => EventsDailyFromArtifact, (e) => e.artifact)
  eventsDailyFromArtifact: EventsDailyFromArtifact[];
  @OneToMany(() => EventsWeeklyFromArtifact, (e) => e.artifact)
  eventsWeeklyFromArtifact: EventsWeeklyFromArtifact[];
  @OneToMany(() => EventsMonthlyFromArtifact, (e) => e.artifact)
  eventsMonthlyFromArtifact: EventsMonthlyFromArtifact[];

  @OneToMany(() => FirstContribution, (event) => event.to)
  firstContributionAsTo: FirstContribution[];
  @OneToMany(() => FirstContribution, (event) => event.from)
  firstContributionAsFrom: FirstContribution[];

  @OneToMany(() => EventPointer, (eventPointer) => eventPointer.artifact)
  eventPointers: EventPointer[];
}

@Entity({ name: "event_type" })
@Index(["name", "version"], { unique: true })
export class EventType extends Base<"EventTypeId"> {
  @Column("varchar", { length: 50 })
  name: string;

  // Allow versioning of events for gradual migrations of data.
  @Column("smallint")
  version: number;

  @OneToMany(() => Event, (event) => event.type)
  events: Event[];
}

type EventId = Brand<number, "EventId">;
@Entity()
@Index(["time"])
@Index(["id", "time"], { unique: true })
@Index(["type", "sourceId", "time"], { unique: true })
export class Event {
  @PrimaryColumn("integer", { generated: "increment" })
  id: EventId;

  @Column("text")
  sourceId: string;

  // The TS property name here is temporary. Will eventually be `type`
  @ManyToOne(() => EventType, (eventType) => eventType.events)
  @JoinColumn({
    name: "typeId",
  })
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

  @Column("jsonb", { default: {} })
  details: Record<string, any>;
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

/******************************
 * MATERIALIZED VIEWS
 * Not all views are possible via TimescaleDB continuous aggregates (e.g. DISTINCT)
 ******************************/

/**
 * For each (to, from) pair, get the first contribution event in time.
 */
@ViewEntity({
  materialized: true,
  expression: `
    SELECT DISTINCT ON ("toId", "fromId")
      "toId",
      "fromId",
      "time",
      "id",
      "typeId",
      "amount"
    FROM "event"
    ORDER BY "toId", "fromId", "time" ASC 
    WITH NO DATA;
  `,
})
export class FirstContribution {
  @ManyToOne(() => Artifact, (artifact) => artifact.firstContributionAsTo)
  @ViewColumn()
  to: Artifact;

  @ManyToOne(() => Artifact, (artifact) => artifact.firstContributionAsFrom, {
    nullable: true,
  })
  @IsOptional()
  @ViewColumn()
  from: Artifact | null;

  @ViewColumn()
  time: Date;

  @ViewColumn()
  id: Brand<number, "EventId">;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  amount: number;
}

/******************************
 * TIMESCALEDB CONTINUOUS AGGREGATES
 ******************************/

/**
 * Continuous aggregations to an artifact
 */
@ViewEntity({
  materialized: true,
  expression: `
    SELECT "toId" AS "artifactId",
      "typeId",
      time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
      SUM(amount) as "amount"
    FROM "event" 
    GROUP BY "artifactId", "typeId", "bucketDaily"
    WITH NO DATA;
  `,
})
export class EventsDailyToArtifact {
  @ManyToOne(() => Artifact, (artifact) => artifact.eventsDailyToArtifact)
  @ViewColumn()
  artifact: Artifact;

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
    SELECT "artifactId",
      "typeId",
      time_bucket(INTERVAL '1 week', "bucketDaily") AS "bucketWeekly",
      SUM(amount) as "amount"
    FROM "events_daily_to_artifact" 
    GROUP BY "artifactId", "typeId", "bucketWeekly"
    WITH NO DATA;
  `,
})
export class EventsWeeklyToArtifact {
  @ManyToOne(() => Artifact, (artifact) => artifact.eventsWeeklyToArtifact)
  @ViewColumn()
  artifact: Artifact;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketWeekly: Date;

  @ViewColumn()
  amount: number;
}

@ViewEntity({
  materialized: true,
  expression: `
    SELECT "artifactId",
      "typeId",
      time_bucket(INTERVAL '1 month', "bucketDaily") AS "bucketMonthly",
      SUM(amount) as "amount"
    FROM "events_daily_to_artifact" 
    GROUP BY "artifactId", "typeId", "bucketMonthly"
    WITH NO DATA;
  `,
})
export class EventsMonthlyToArtifact {
  @ManyToOne(() => Artifact, (artifact) => artifact.eventsMonthlyToArtifact)
  @ViewColumn()
  artifact: Artifact;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketMonthly: Date;

  @ViewColumn()
  amount: number;
}

/**
 * Continuous aggregations to a project
 */
@ViewEntity({
  materialized: true,
  expression: `
    SELECT "projectId",
      "typeId",
      time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
      SUM(amount) as "amount"
    FROM "event"
    INNER JOIN "project_artifacts_artifact"
      on "project_artifacts_artifact"."artifactId" = "event"."toId"
    GROUP BY "projectId", "typeId", "bucketDaily"
    WITH NO DATA;
  `,
})
export class EventsDailyToProject {
  @ManyToOne(() => Project, (project) => project.eventsDailyToProject)
  @ViewColumn()
  project: Project;

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
      "typeId",
      time_bucket(INTERVAL '1 week', "bucketDaily") AS "bucketWeekly",
      SUM(amount) as "amount"
    FROM "events_daily_to_project" 
    GROUP BY "projectId", "typeId", "bucketWeekly"
    WITH NO DATA;
  `,
})
export class EventsWeeklyToProject {
  @ManyToOne(() => Project, (project) => project.eventsWeeklyToProject)
  @ViewColumn()
  project: Project;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketWeekly: Date;

  @ViewColumn()
  amount: number;
}

@ViewEntity({
  materialized: true,
  expression: `
    SELECT "projectId",
      "typeId",
      time_bucket(INTERVAL '1 month', "bucketDaily") AS "bucketMonthly",
      SUM(amount) as "amount"
    FROM "events_daily_to_project" 
    GROUP BY "projectId", "typeId", "bucketMonthly"
    WITH NO DATA;
  `,
})
export class EventsMonthlyToProject {
  @ManyToOne(() => Project, (project) => project.eventsMonthlyToProject)
  @ViewColumn()
  project: Project;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketMonthly: Date;

  @ViewColumn()
  amount: number;
}

/**
 * Continuous aggregates from an artifact
 */
@ViewEntity({
  materialized: true,
  expression: `
    SELECT "fromId" AS "artifactId",
      "typeId",
      time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
      SUM(amount) as "amount"
    FROM "event" 
    GROUP BY "artifactId", "typeId", "bucketDaily"
    WITH NO DATA;
  `,
})
export class EventsDailyFromArtifact {
  @ManyToOne(() => Artifact, (artifact) => artifact.eventsDailyFromArtifact)
  @ViewColumn()
  artifact: Artifact;

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
    SELECT "artifactId",
      "typeId",
      time_bucket(INTERVAL '1 week', "bucketDaily") AS "bucketWeekly",
      SUM(amount) as "amount"
    FROM "events_daily_from_artifact" 
    GROUP BY "artifactId", "typeId", "bucketWeekly"
    WITH NO DATA;
  `,
})
export class EventsWeeklyFromArtifact {
  @ManyToOne(() => Artifact, (artifact) => artifact.eventsWeeklyFromArtifact)
  @ViewColumn()
  artifact: Artifact;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketWeekly: Date;

  @ViewColumn()
  amount: number;
}

@ViewEntity({
  materialized: true,
  expression: `
    SELECT "artifactId",
      "typeId",
      time_bucket(INTERVAL '1 month', "bucketDaily") AS "bucketMonthly",
      SUM(amount) as "amount"
    FROM "events_daily_from_artifact" 
    GROUP BY "artifactId", "typeId", "bucketMonthly"
    WITH NO DATA;
  `,
})
export class EventsMonthlyFromArtifact {
  @ManyToOne(() => Artifact, (artifact) => artifact.eventsMonthlyFromArtifact)
  @ViewColumn()
  artifact: Artifact;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketMonthly: Date;

  @ViewColumn()
  amount: number;
}

/**
 * Continuous aggregates from a project
 */
@ViewEntity({
  materialized: true,
  expression: `
    SELECT "projectId",
      "typeId",
      time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
      SUM(amount) as "amount"
    FROM "event"
    INNER JOIN "project_artifacts_artifact"
      on "project_artifacts_artifact"."artifactId" = "event"."fromId"
    GROUP BY "projectId", "typeId", "bucketDaily"
    WITH NO DATA;
  `,
})
export class EventsDailyFromProject {
  @ManyToOne(() => Project, (project) => project.eventsDailyFromProject)
  @ViewColumn()
  project: Project;

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
      "typeId",
      time_bucket(INTERVAL '1 week', "bucketDaily") AS "bucketWeekly",
      SUM(amount) as "amount"
    FROM "events_daily_from_project" 
    GROUP BY "projectId", "typeId", "bucketWeekly"
    WITH NO DATA;
  `,
})
export class EventsWeeklyFromProject {
  @ManyToOne(() => Project, (project) => project.eventsWeeklyFromProject)
  @ViewColumn()
  project: Project;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketWeekly: Date;

  @ViewColumn()
  amount: number;
}

@ViewEntity({
  materialized: true,
  expression: `
    SELECT "projectId",
      "typeId",
      time_bucket(INTERVAL '1 month', "bucketDaily") AS "bucketMonthly",
      SUM(amount) as "amount"
    FROM "events_daily_from_project" 
    GROUP BY "projectId", "typeId", "bucketMonthly"
    WITH NO DATA;
  `,
})
export class EventsMonthlyFromProject {
  @ManyToOne(() => Project, (project) => project.eventsMonthlyFromProject)
  @ViewColumn()
  project: Project;

  @ViewColumn()
  type: EventType;

  @ViewColumn()
  bucketMonthly: Date;

  @ViewColumn()
  amount: number;
}
