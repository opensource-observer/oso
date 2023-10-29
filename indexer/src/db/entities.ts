import _ from "lodash";
import {
  Artifact,
  ArtifactType,
  ArtifactNamespace,
  Project as DBProject,
  Collection as DBCollection,
  CollectionType,
} from "./orm-entities.js";
import { Project, Collection, URL, BlockchainAddress } from "oss-directory";
import { logger } from "../utils/logger.js";
import {
  isGitHubOrg,
  isGitHubRepo,
  parseGitHubUrl,
  parseNpmUrl,
} from "../utils/parsing.js";
import { getNpmUrl } from "../utils/format.js";
import { safeCast, ensure, filterFalsy } from "../utils/common.js";
import { getOwnerRepos } from "../collectors/github/get-org-repos.js";
import { ProjectRepository } from "./project.js";
import { CollectionRepository } from "./collection.js";
import { In } from "typeorm";
import { ArtifactRepository } from "./artifacts.js";
import { AppDataSource } from "./data-source.js";

/**
 * Upsert a Collection from oss-directory
 * Pre-condition: all of the project slugs need to already be in the database
 * @param ossCollection
 */
async function ossUpsertCollection(ossCollection: Collection) {
  const { slug, name, projects: projectSlugs } = ossCollection;

  // Get all of the projects
  const projects = await ProjectRepository.find({
    where: {
      slug: In(projectSlugs),
    },
  });

  // Check that all Projects are already in the database
  if (projects.length != projectSlugs.length) {
    logger.warn(
      `Not all of the projects for collection ${slug} are in the database. Please add all projects first`,
    );
  }
  // Get collection type OSS_DIRECTORY
  const collectionType = await AppDataSource.getRepository(
    CollectionType,
  ).findOneOrFail({
    where: {
      name: "OSS_DIRECTORY",
    },
  });

  // Upsert into the database
  return await AppDataSource.transaction(async (manager) => {
    const collectionResult = await manager
      .withRepository(CollectionRepository)
      .upsert(
        {
          name: name,
          slug: slug,
          type: collectionType,
        },
        ["slug"],
      );

    // Manage all the relations for each of the projects
    const collection = await manager.getRepository(DBCollection).findOneOrFail({
      relations: {
        projects: true,
      },
      where: {
        id: collectionResult.identifiers[0].id,
      },
    });

    const currentProjectIds = collection.projects.map((p) => p.id);
    const intendedProjectIds = projects.map((p) => p.id);

    // intended - current = new
    const newProjectIds = _.difference(intendedProjectIds, currentProjectIds);

    // current - intended = removed
    const removedProjectIds = _.difference(
      currentProjectIds,
      intendedProjectIds,
    );

    // Add new
    await manager
      .createQueryBuilder()
      .relation(DBCollection, "projects")
      .of(collection.id)
      .add(newProjectIds);

    // Delete removed
    await manager
      .createQueryBuilder()
      .relation(DBCollection, "projects")
      .of(collection.id)
      .remove(removedProjectIds);

    return {
      added: newProjectIds.length,
      removed: removedProjectIds.length,
      new: intendedProjectIds.length,
      old: currentProjectIds.length,
      ids: intendedProjectIds,
      collection: collection,
    };
  });
}

/**
 * Upsert a Project from oss-directory
 * @param ossProj
 * @returns
 */
async function ossUpsertProject(ossProj: Project) {
  const { slug, name, github, npm, blockchain } = ossProj;

  // Create all of the missing artifacts first
  // Note: this will only create missing artifacts, not update existing ones
  const artifacts = [
    // Create GitHub artifacts
    ...(await ossCreateGitHubArtifacts(github)),
    // Create npm artifacts
    ...(await ossCreateNpmArtifacts(npm)),
    // Create Optimism artifacts
    ...(await ossCreateBlockchainArtifacts(blockchain)),
  ];

  // Then upsert the project with the relations
  return await AppDataSource.transaction(async (manager) => {
    const repo = manager.withRepository(ProjectRepository);
    const projectResult = await repo.upsert(
      [
        {
          slug: slug,
          name: name,
        },
      ],
      ["slug"],
    );

    const project = await repo.findOneOrFail({
      relations: {
        artifacts: true,
      },
      where: {
        id: projectResult.identifiers[0].id,
      },
    });

    const currentArtifactIds = project.artifacts.map((a) => a.id);
    const intendedArtifactIds = artifacts.map((a) => a.id);

    const newArtifactIds = _.difference(
      intendedArtifactIds,
      currentArtifactIds,
    );
    const removedArtifactIds = _.difference(
      currentArtifactIds,
      intendedArtifactIds,
    );

    // Update all artifact relations
    await manager
      .createQueryBuilder()
      .relation(DBProject, "artifacts")
      .of(project.id)
      .add(newArtifactIds);

    // Delete removed artifacts
    await manager
      .createQueryBuilder()
      .relation(DBProject, "artifacts")
      .of(project.id)
      .remove(removedArtifactIds);

    return {
      old: intendedArtifactIds.length,
      new: currentArtifactIds.length,
      added: newArtifactIds.length,
      removed: removedArtifactIds.length,
      ids: intendedArtifactIds,
      project: project,
    };
  });

  // FIXME this needs to be added back in.
  // Remove any artifact relations that are no longer valid
  /*
  await prisma.projectsOnArtifacts.deleteMany({
    where: {
      projectId: project.id,
      artifactId: {
        notIn: artifacts.map((a) => a.id),
      },
    },
  });
  */

  //return project;
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
  const orgRepos = _.flatten(await Promise.all(orgNames.map(getOwnerRepos)));
  const orgRepoUrls = orgRepos.filter((r) => !r.isFork).map((r) => r.url);
  const allRepos = [...repoUrls, ...orgRepoUrls];
  const parsedRepos = allRepos.map(parseGitHubUrl);
  const data = parsedRepos.map((p) => ({
    type: ArtifactType.GIT_REPOSITORY,
    namespace: ArtifactNamespace.GITHUB,
    name: ensure<string>(
      p?.slug.toLowerCase(),
      `Invalid parsed GitHub URL: ${p}`,
    ),
    url: ensure<string>(
      p?.url.toLowerCase(),
      `Invalid parsed GitHub URL: ${p}`,
    ),
  }));
  const slugs = filterFalsy(parsedRepos.map((p) => p?.slug.toLowerCase()));

  const newArtifacts = Artifact.create(data);
  logger.debug("Upserting artifacts");
  // Create records
  const result = await ArtifactRepository.upsertMany(newArtifacts);
  const createCount = result.identifiers.length;

  logger.debug(
    `... created ${createCount}/${data.length} GitHub artifacts (skip duplicates)`,
  );

  // Now get all of the artifacts
  const artifacts = ArtifactRepository.find({
    where: {
      type: ArtifactType.GIT_REPOSITORY,
      namespace: ArtifactNamespace.GITHUB,
      name: In(slugs),
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
    name: ensure<string>(p?.slug.toLowerCase(), `Invalid parsed npm URL: ${p}`),
    url: ensure<string>(p?.url, `Invalid parsed npm URL: ${p}`),
  }));
  const slugs = filterFalsy(parsed.map((p) => p?.slug.toLowerCase()));

  // Create records
  const result = await ArtifactRepository.upsertMany(data);
  const createCount = result.identifiers.length;
  logger.debug(
    `... inserted ${createCount}/${data.length} npm artifacts (skip duplicates)`,
  );

  // Now get all of the artifacts
  const artifacts = await ArtifactRepository.find({
    where: {
      type: ArtifactType.NPM_PACKAGE,
      namespace: ArtifactNamespace.NPM_REGISTRY,
      name: In(slugs),
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
async function ossCreateBlockchainArtifacts(addrObjects?: BlockchainAddress[]) {
  if (!addrObjects) {
    return safeCast<Artifact[]>([]);
  }

  const typeMap: { [key: string]: ArtifactType } = {
    eoa: ArtifactType.EOA_ADDRESS,
    safe: ArtifactType.SAFE_ADDRESS,
    factory: ArtifactType.FACTORY_ADDRESS,
    contract: ArtifactType.CONTRACT_ADDRESS,
  };
  const typeResolutionOrder = ["eoa", "safe", "factory", "contract"];
  const typeResolver = (tags: string[]) => {
    for (const type of typeResolutionOrder) {
      if (tags.indexOf(type) !== -1) {
        return typeMap[type];
      }
    }
    return typeMap["eoa"];
  };

  const data = addrObjects.flatMap((o) => {
    return o.networks.map((network) => {
      return {
        type: typeResolver(o.tags),
        // Hacky solution for now. We should we address after the typeorm migration
        namespace:
          network === "optimism"
            ? ArtifactNamespace.OPTIMISM
            : ArtifactNamespace.ETHEREUM,
        // Normalize the addresses to lowercase
        name: o.address.toLowerCase(),
      };
    });
  });
  const addresses = data.map((d) => d.name);

  // Create records
  const result = await ArtifactRepository.upsertMany(data);
  const createCount = result.identifiers.length;
  logger.debug(
    `... inserted ${createCount}/${data.length} blockchain artifacts (skip duplicates)`,
  );

  // Now get all of the artifacts
  const artifacts = await ArtifactRepository.find({
    where: {
      name: In(addresses),
    },
  });
  return artifacts;
}

/**
 * Gets a collection by a slug
 * @param slug
 * @returns
 */
async function getCollectionBySlug(slug: string) {
  return await CollectionRepository.findOne({ where: { slug } });
}

/**
 * Gets a project by a slug
 * @param slug
 * @returns
 */
async function getProjectBySlug(slug: string) {
  return await ProjectRepository.findOne({ where: { slug } });
}

/**
 * Gets an artifact by name
 * @param fields
 * @returns
 */
async function getArtifactByName(fields: {
  namespace: ArtifactNamespace;
  name: string;
}): Promise<Artifact | null> {
  const { namespace, name } = fields;
  const result = await ArtifactRepository.findOne({
    where: {
      namespace: namespace,
      name: name,
    },
  });
  return result;
}

/**
 * Generic upsert for an artifact
 * @param address
 * @param type
 * @param ns
 * @returns
 */
async function upsertArtifact(fields: {
  namespace: ArtifactNamespace;
  type: ArtifactType;
  name: string;
  url?: string;
  details?: any;
}) {
  return await ArtifactRepository.upsert(
    [{ ...fields }],
    ["name", "namespace"],
  );
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
    name: slug.toLowerCase(),
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
  getCollectionBySlug,
  getProjectBySlug,
  getArtifactByName,
  ossUpsertProject,
  ossUpsertCollection,
  upsertGitHubRepo,
  upsertNpmPackage,
};
