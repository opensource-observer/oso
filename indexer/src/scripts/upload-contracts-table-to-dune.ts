import { In } from "typeorm";
import { AppDataSource } from "../db/data-source.js";
import {
  Artifact,
  ArtifactNamespace,
  ArtifactType,
} from "../db/orm-entities.js";
import { ProjectRepository } from "../db/project.js";
import fetch from "node-fetch";
import { DUNE_API_KEY } from "../config.js";
import { writeFile } from "fs/promises";
import { UniqueArray } from "../utils/array.js";
import { generateSourceIdFromArray } from "../utils/source-ids.js";

export async function main() {
  await AppDataSource.initialize();

  const projects = await ProjectRepository.find({
    relations: {
      artifacts: true,
    },
    where: {
      artifacts: {
        type: In([ArtifactType.CONTRACT_ADDRESS]),
        namespace: ArtifactNamespace.OPTIMISM,
      },
    },
  });
  const allArtifacts = projects.flatMap((p) => p.artifacts);

  const uniqueArtifacts = new UniqueArray((a: Artifact) => a.id);
  allArtifacts.forEach((a) => uniqueArtifacts.push(a));
  const sortedUniqueArtifacts = uniqueArtifacts.items();
  // Sort by creation
  sortedUniqueArtifacts.sort(
    (a, b) => a.createdAt.getTime() - b.createdAt.getTime(),
  );

  const rows = ["id,address"];
  rows.push(
    ...sortedUniqueArtifacts.map((a) => {
      return `${a.id},${a.name}`;
    }),
  );
  const artifactsCsv = rows.join("\n");

  if (sortedUniqueArtifacts.length === 0) {
    throw new Error("expecting artifacts. have none");
  }

  const contractsCsvSha1 = generateSourceIdFromArray([artifactsCsv]);

  await writeFile(
    `contracts-${contractsCsvSha1}-${sortedUniqueArtifacts[0].id}-${
      sortedUniqueArtifacts.slice(-1)[0].id
    }.csv`,
    artifactsCsv,
    { encoding: "utf-8" },
  );

  await new Promise<void>((resolve) => {
    console.log("about to upload");
    console.log(`sha1=${contractsCsvSha1}`);
    console.log(`count=${sortedUniqueArtifacts.length}`);
    setTimeout(() => {
      console.log("uploading....");
      resolve();
    }, 30000);
  });

  const tableName = `oso_optimism_contracts_${contractsCsvSha1}`;

  const uploader = new DuneCSVUploader(DUNE_API_KEY);
  const response = await uploader.upload(
    tableName,
    `OSO monitored optimism contracts: ${contractsCsvSha1}.`,
    rows,
  );
  if (response.status !== 200) {
    console.log("failed to upload to the contracts");
    process.exit(1);
  }
  console.log(`uploaded to ${tableName}`);
}

class DuneCSVUploader {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async upload(tableName: string, description: string, rows: string[]) {
    return await fetch("https://api.dune.com/api/v1/table/upload/csv", {
      method: "POST",
      body: JSON.stringify({
        table_name: tableName,
        description: description,
        data: rows.join("\n"),
      }),
      headers: {
        "Content-Type": "application/json",
        "X-Dune-Api-Key": this.apiKey,
      },
    });
  }
}

main().catch((err) => {
  console.log(err);
});
