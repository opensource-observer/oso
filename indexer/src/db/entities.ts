import _ from "lodash";
import { ArtifactType, ArtifactNamespace } from "@prisma/client";
import { Project, Collection, URL, BlockchainAddress } from "oss-directory";
import { prisma } from "./prisma-client.js";
import { logger } from "../utils/logger.js";
import { parseGitHubUrl, parseNpmUrl } from "../utils/parsing.js";
import { getNpmUrl } from "../utils/format.js";
import { safeCast, filterFalsy } from "../utils/common.js";
import { getOrgRepos } from "../events/github/getOrgRepos.js";
import { HandledError } from "../utils/error.js";

/**
 * Upsert a Collection from oss-directory
 * Pre-condition: all of the project slugs need to already be in the database
 * @param ossCollection
 */
async function upsertOssCollection(ossCollection: Collection) {
  const { slug, name, projects: projectSlugs } = ossCollection;

  // Get all of the projects
  const projects = await prisma.project.findMany({
    where: {
      slug: {
        in: projectSlugs,
      },
    },
  });

  if (projects.length != projectSlugs.length) {
    throw new HandledError(
      `Could not find all projects for collection ${slug}. Please add all projects first`,
    );
  }

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
async function upsertOssProject(ossProj: Project) {
  const { slug, name, github, npm, optimism } = ossProj;

  const expand = async <P, R>(
    f: (p: P) => Promise<R>,
    params?: P[],
  ): Promise<R[]> =>
    !params ? safeCast<R[]>([]) : _.flatten(await Promise.all(params.map(f)));

  // Upsert all of the adderss and npm artifacts first
  const artifacts = filterFalsy([
    // Enumerate npm artifacts
    ...(await expand(upsertOssNpm, npm)),
    // Enumerate Optimism artifacts
    ...(await expand(
      (a) => upsertOssBlockchainAddress(a, ArtifactNamespace.OPTIMISM),
      optimism,
    )),
  ]);

  // Enumerate GitHub artifacts
  if (github) {
    for (const githubUrl of github) {
      const githubArtifacts = await upsertOssGitHub(githubUrl);
      if (githubArtifacts) {
        artifacts.push(...githubArtifacts);
      }
    }
  }

  // Then upsert the project with the relations
  const update = {
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
    create: {
      slug,
      ...update,
    },
  });
  return project;
}

/**
 * Upsert a GitHub resource from oss-directory
 */
async function upsertOssGitHub(ossUrl: URL) {
  const { url } = ossUrl;
  const { slug, owner, repo } = parseGitHubUrl(url) ?? {};

  if (!slug || !owner) {
    logger.warn(`Invalid GitHub URL: ${url}`);
    return;
  }

  // If there is a single repo specified, just get that
  if (repo) {
    return [await upsertGitHubRepo(slug, url)];
  }

  // Otherwise, get all repos for the org
  return await upsertGitHubOrg(owner);
}

/**
 * Upsert all of the repos in an organization
 */
async function upsertGitHubOrg(owner: string) {
  const repos = await getOrgRepos(owner);
  return await Promise.all(
    repos.map((r) => upsertGitHubRepo(r.nameWithOwner, r.url)),
  );
}

/**
 * Upsert a GitHub repo artifact
 * @param slug
 * @param url
 * @returns
 */
async function upsertGitHubRepo(slug: string, url: string) {
  return await prisma.artifact.upsert({
    where: {
      type_namespace_name: {
        type: ArtifactType.GIT_REPOSITORY,
        namespace: ArtifactNamespace.GITHUB,
        name: slug,
      },
    },
    update: {},
    create: {
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
      name: slug,
      url,
    },
  });
}

/**
 * Upsert an npm artifact from oss-directory
 * @param ossUrl
 * @returns
 */
async function upsertOssNpm(ossUrl: URL) {
  const { url } = ossUrl;
  const { slug } = parseNpmUrl(url) ?? {};

  if (!slug) {
    logger.warn(`Invalid npm URL: ${url}`);
    return;
  }

  return await upsertNpmPackage(slug);
}

/**
 * Upsert an npm package artifact
 * @param packageName
 * @returns
 */
async function upsertNpmPackage(packageName: string) {
  return await prisma.artifact.upsert({
    where: {
      type_namespace_name: {
        type: ArtifactType.NPM_PACKAGE,
        namespace: ArtifactNamespace.NPM_REGISTRY,
        name: packageName,
      },
    },
    update: {},
    create: {
      type: ArtifactType.NPM_PACKAGE,
      namespace: ArtifactNamespace.NPM_REGISTRY,
      name: packageName,
      url: getNpmUrl(packageName),
    },
  });
}

/**
 * Upsert a blockchain address artifact from oss-directory
 * @param ossAddr
 * @param artifactNamespace
 * @returns
 */
async function upsertOssBlockchainAddress(
  ossAddr: BlockchainAddress,
  artifactNamespace: ArtifactNamespace,
) {
  const { address, type } = ossAddr;
  const artifactType =
    type === "eoa"
      ? ArtifactType.EOA_ADDRESS
      : type === "safe"
      ? ArtifactType.SAFE_ADDRESS
      : type === "contract"
      ? ArtifactType.CONTRACT_ADDRESS
      : type === "factory"
      ? ArtifactType.FACTORY_ADDRESS
      : ArtifactType.EOA_ADDRESS;
  return await upsertBlockchainAddress(
    address,
    artifactType,
    artifactNamespace,
  );
}

/**
 * Upsert a blockchain address artifact
 * @param address
 * @param type
 * @param ns
 * @returns
 */
async function upsertBlockchainAddress(
  address: string,
  type: ArtifactType,
  ns: ArtifactNamespace,
) {
  return await prisma.artifact.upsert({
    where: {
      type_namespace_name: {
        type,
        namespace: ns,
        name: address,
      },
    },
    update: {},
    create: {
      type,
      namespace: ns,
      name: address,
    },
  });
}

export { upsertOssProject, upsertOssCollection, upsertNpmPackage };
