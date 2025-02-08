import path from "node:path";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { glob } from "glob";
import * as yaml from "yaml";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// YAML file extension
const EXTENSION = ".hml";
const DOCUMENT_PREFIX = "---\n";
const DOCUMENT_POSTFIX = "";
const DOCUMENT_DELIMITER = "\n";

// Where to store all table configs
const metadataDir = path.resolve(__dirname, "../oso_subgraph/metadata/");
// Should map to the tables field in ./metadata/databases/databases.yaml
const metadataGlob = path.format({
  dir: metadataDir,
  name: "*",
  ext: EXTENSION,
});

// Schema for Hasura table configuration
type ModelPermissions = {
  kind: "ModelPermissions";
  version: string;
  definition: {
    modelName: string;
    permissions: {
      role: string;
      select: {
        filter: null;
      };
    }[];
  };
};

type TypePermissions = {
  kind: "TypePermissions";
  version: string;
  definition: {
    typeName: string;
    permissions: {
      role: string;
      output: {
        allowedFields: string[];
      };
    }[];
  };
};

const ensureModelPermissions = (obj: Partial<ModelPermissions>) => {
  if (!obj?.definition?.permissions) {
    throw new Error("Malformed ModelPermissions");
  }
  // Skip if already has anonymous permission
  const hasAnon = obj.definition.permissions.find(
    (p) => p.role === "anonymous",
  );
  if (hasAnon) {
    return { ...obj };
  }

  // Add anonymous permission
  return {
    ...obj,
    definition: {
      ...obj.definition,
      permissions: [
        ...obj.definition.permissions,
        {
          role: "anonymous",
          select: { filter: null },
        },
      ],
    },
  };
};

const ensureTypePermissions = (obj: Partial<TypePermissions>) => {
  if (!obj?.definition?.permissions) {
    throw new Error("Malformed TypePermissions");
  }

  // We need the admin permission to copy from
  const adminPerm = obj.definition.permissions.find((p) => p.role === "admin");
  if (!adminPerm) {
    throw new Error("TypePermissions must have pre-existing admin permission");
  }

  // Exclude any pre-existing anonymous permissions
  const permsWithoutAnon = obj.definition.permissions.filter(
    (p) => p.role !== "anonymous",
  );

  // Copy admin permission to anonymous permissions
  return {
    ...obj,
    definition: {
      ...obj.definition,
      permissions: [
        ...permsWithoutAnon,
        {
          role: "anonymous",
          output: {
            allowedFields: [...adminPerm.output.allowedFields],
          },
        },
      ],
    },
  };
};

const ensureDocument = (obj: any) => {
  if (obj?.kind === "ModelPermissions") {
    return ensureModelPermissions(obj);
  } else if (obj?.kind === "TypePermissions") {
    return ensureTypePermissions(obj);
  } else {
    return obj;
  }
};

async function main(): Promise<void> {
  // Scan all metadata files
  //const allFiles = await fs.readdir(metadataDir, { recursive: false });
  const allFiles = await glob(metadataGlob);
  console.log(allFiles);
  for (const file of allFiles) {
    console.log(`Updating ${file}...`);
    const strContents = await fs.readFile(file);
    const docs = yaml.parseAllDocuments(strContents.toString());
    const newDocs = docs.map((doc) => {
      const docObj = doc.toJSON();
      return ensureDocument(docObj);
    });
    const newStrings = newDocs.map(
      (d) => DOCUMENT_PREFIX + yaml.stringify(d) + DOCUMENT_POSTFIX,
    );
    const newFile = newStrings.join(DOCUMENT_DELIMITER);
    await fs.writeFile(file, newFile);
  }
}

main()
  .then(() => console.log("Done"))
  .catch((e) => {
    //console.warn(e);
    throw e;
  });
