import _ from "lodash";
import { Artifact, ArtifactType, ArtifactNamespace } from "@prisma/client";
import { Project, Collection, URL, BlockchainAddress } from "oss-directory";
import { prisma } from "./prisma-client.js";
import { logger } from "../utils/logger.js";
import {
  isGitHubOrg,
  isGitHubRepo,
  parseGitHubUrl,
  parseNpmUrl,
} from "../utils/parsing.js";
import { getNpmUrl } from "../utils/format.js";
import { safeCast, ensure, filterFalsy } from "../utils/common.js";
import { getOrgRepos } from "../events/github/getOrgRepos.js";
import { HandledError } from "../utils/error.js";

/**
 * Upsert a Collection from oss-directory
 * Pre-condition: all of the project slugs need to already be in the database
 * @param ossCollection
 */
async function ossUpsertCollection(ossCollection: Collection) {
  const { slug, name, projects: projectSlugs } = ossCollection;

  // Get all of the projects
  const projects = await prisma.project.findMany({
    where: {
      slug: {
        in: projectSlugs,
      },
    },
  });

  // Check that all Projects are already in the database
  if (projects.length != projectSlugs.length) {
    throw new HandledError(
      `Could not find all projects for collection ${slug}. Please add all projects first`,
    );
  }

  // Upsert into the database
  const update = {
    name,
    projects: {
      createMany: {
        data: projects.map((p) => ({
          projectId: p.id,
        })),
        skipDuplicates: true,
      },
    },
  };
  const collection = await prisma.collection.upsert({
    where: { slug },
    update: { ...update },
    create: {
      slug,
      ...update,
    },
  });
  return collection;
}

/**
 * Upsert a Project from oss-directory
 * @param ossProj
 * @returns
 */
async function ossUpsertProject(ossProj: Project) {
  const { slug, name, github, npm, optimism } = ossProj;

  // Create all of the missing artifacts first
  // Note: this will only create missing artifacts, not update existing ones
  const artifacts = [
    // Create GitHub artifacts
    ...(await ossCreateGitHubArtifacts(github)),
    // Create npm artifacts
    ...(await ossCreateNpmArtifacts(npm)),
    // Create Optimism artifacts
    ...(await ossCreateBlockchainArtifacts(
      ArtifactNamespace.OPTIMISM,
      optimism,
    )),
  ];

  // Then upsert the project with the relations
  const update = {
    slug,
    name,
    artifacts: {
      createMany: {
        data: artifacts.map((a) => ({
          artifactId: a.id,
        })),
        skipDuplicates: true,
      },
    },
  };
  const project = await prisma.project.upsert({
    where: { slug },
    update: { ...update },
    create: { ...update },
  });
  return project;
}

/**
 * Upsert a GitHub resource from oss-directory
 */
async function ossCreateGitHubArtifacts(
  urlObjects?: URL[],
): Promise<Artifact[]> {
  if (!urlObjects) {
    return safeCast<Artifact[]>([]);
  }

  const urls = urlObjects.map((o) => o.url);
  const repoUrls = urls.filter(isGitHubRepo);
  const orgUrls = urls.filter(isGitHubOrg);

  // Check for invalid URLs
  if (orgUrls.length + repoUrls.length !== urls.length) {
    const nonConfirmingUrls = urls.filter(
      (u) => !isGitHubOrg(u) && !isGitHubRepo(u),
    );
    const sep = "\n\t";
    logger.warn(`Invalid GitHub URLs:${sep}${nonConfirmingUrls.join(sep)}`);
  }

  // Flatten all GitHub orgs
  const orgNames = filterFalsy(
    orgUrls.map(parseGitHubUrl).map((p) => p?.owner),
  );
  const orgRepos = _.flatten(await Promise.all(orgNames.map(getOrgRepos)));
  const orgRepoUrls = orgRepos.map((r) => r.url);
  const allRepos = [...repoUrls, ...orgRepoUrls];
  const parsedRepos = allRepos.map(parseGitHubUrl);
  const data = parsedRepos.map((p) => ({
    type: ArtifactType.GIT_REPOSITORY,
    namespace: ArtifactNamespace.GITHUB,
    name: ensure<string>(p?.slug, `Invalid parsed GitHub URL: ${p}`),
    url: ensure<string>(p?.url, `Invalid parsed GitHub URL: ${p}`),
  }));
  const slugs = filterFalsy(parsedRepos.map((p) => p?.slug));

  // Create records
  const { count: createCount } = await prisma.artifact.createMany({
    data,
    skipDuplicates: true,
  });
  logger.debug(
    `... created ${createCount}/${data.length} GitHub artifacts (skip duplicates)`,
  );

  // Now get all of the artifacts
  const artifacts = await prisma.artifact.findMany({
    where: {
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
      name: {
        in: slugs,
      },
    },
  });
  return artifacts;
}

/**
 * Upsert an npm artifact from oss-directory
 * @param ossUrl
 * @returns
 */
async function ossCreateNpmArtifacts(urlObjects?: URL[]) {
  if (!urlObjects) {
    return safeCast<Artifact[]>([]);
  }

  const urls = urlObjects.map((o) => o.url);
  const parsed = urls.map(parseNpmUrl);
  const data = parsed.map((p) => ({
    type: ArtifactType.NPM_PACKAGE,
    namespace: ArtifactNamespace.NPM_REGISTRY,
    name: ensure<string>(p?.slug, `Invalid parsed npm URL: ${p}`),
    url: ensure<string>(p?.url, `Invalid parsed npm URL: ${p}`),
  }));
  const slugs = filterFalsy(parsed.map((p) => p?.slug));

  // Create records
  const { count: createCount } = await prisma.artifact.createMany({
    data,
    skipDuplicates: true,
  });
  logger.debug(
    `... inserted ${createCount}/${data.length} npm artifacts (skip duplicates)`,
  );

  // Now get all of the artifacts
  const artifacts = await prisma.artifact.findMany({
    where: {
      type: ArtifactType.NPM_PACKAGE,
      namespace: ArtifactNamespace.NPM_REGISTRY,
      name: {
        in: slugs,
      },
    },
  });
  return artifacts;
}

/**
 * Upsert a blockchain address artifact from oss-directory
 * @param ossAddr
 * @param artifactNamespace
 * @returns
 */
async function ossCreateBlockchainArtifacts(
  namespace: ArtifactNamespace,
  addrObjects?: BlockchainAddress[],
) {
  if (!addrObjects) {
    return safeCast<Artifact[]>([]);
  }

  const data = addrObjects.map((o) => ({
    type:
      o.type === "eoa"
        ? ArtifactType.EOA_ADDRESS
        : o.type === "safe"
        ? ArtifactType.SAFE_ADDRESS
        : o.type === "contract"
        ? ArtifactType.CONTRACT_ADDRESS
        : o.type === "factory"
        ? ArtifactType.FACTORY_ADDRESS
        : ArtifactType.EOA_ADDRESS,
    namespace,
    name: o.address,
  }));
  const addresses = data.map((d) => d.name);

  // Create records
  const { count: createCount } = await prisma.artifact.createMany({
    data,
    skipDuplicates: true,
  });
  logger.debug(
    `... inserted ${createCount}/${data.length} blockchain artifacts (skip duplicates)`,
  );

  // Now get all of the artifacts
  const artifacts = await prisma.artifact.findMany({
    where: {
      namespace,
      name: {
        in: addresses,
      },
    },
  });
  return artifacts;
}

/**
 * Generic upsert for an artifact
 * @param address
 * @param type
 * @param ns
 * @returns
 */
async function upsertArtifact(fields: {
  type: ArtifactType;
  namespace: ArtifactNamespace;
  name: string;
  url?: string;
  details?: any;
}) {
  return await prisma.artifact.upsert({
    where: {
      type_namespace_name: {
        type: fields.type,
        namespace: fields.namespace,
        name: fields.name,
      },
    },
    update: { ...fields },
    create: { ...fields },
  });
}

/**
 * Upsert a GitHub repo artifact
 * @param slug
 * @param url
 * @returns
 */
async function upsertGitHubRepo(slug: string, url: string) {
  return await upsertArtifact({
    type: ArtifactType.GIT_REPOSITORY,
    namespace: ArtifactNamespace.GITHUB,
    name: slug,
    url,
  });
}

/**
 * Upsert an npm package artifact
 * @param packageName
 * @returns
 */
async function upsertNpmPackage(packageName: string) {
  return await upsertArtifact({
    type: ArtifactType.NPM_PACKAGE,
    namespace: ArtifactNamespace.NPM_REGISTRY,
    name: packageName,
    url: getNpmUrl(packageName),
  });
}

export {
  ossUpsertProject,
  ossUpsertCollection,
  upsertGitHubRepo,
  upsertNpmPackage,
};
