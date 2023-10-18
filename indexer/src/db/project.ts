import { In } from "typeorm";
import { AppDataSource } from "./data-source.js";
import { ArtifactType, Project } from "./orm-entities.js";

export const ProjectRepository = AppDataSource.getRepository(Project).extend({
  async allFundableProjectsWithAddresses() {
    return await this.find({
      relations: {
        artifacts: true,
      },
      where: {
        artifacts: {
          type: In([ArtifactType.EOA_ADDRESS, ArtifactType.SAFE_ADDRESS]),
        },
      },
    });
  },
  async nonCanonical() {
    const sumString =
      'SUM(CASE WHEN LOWER(p."slug") = p."slug" THEN 0 ELSE 1 END)';
    return (await this.manager
      .createQueryBuilder()
      .select()
      .addSelect('p."name"', "name")
      .addSelect('p."slug"', "slug")
      .addSelect(sumString, "nonCanonicalCount")
      .from(Project, "p")
      .groupBy("1,2")
      .having(`${sumString} > 0`)
      .getRawMany()) as {
      name: string;
      slug: string;
      nonCanonicalCount: number;
    }[];
  },
  // Find any duplicates
  async duplicates() {
    return (await this.manager
      .createQueryBuilder()
      .select()
      .addSelect('lower(p."name")', "name")
      .addSelect('lower(p."slug")', "slug")
      .addSelect('count(p."id")', "count")
      .addSelect('array_agg(p."id")', "ids")
      .addSelect('array_agg(p."name")', "names")
      .from(Project, "p")
      .groupBy("1,2")
      .having('count(p."id") > 1')
      .getRawMany()) as {
      name: string;
      slug: string;
      count: number;
      ids: number[];
      names: string[];
    }[];
  },
});
