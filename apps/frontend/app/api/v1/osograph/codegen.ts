import { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  schema: "app/api/v1/osograph/schema/graphql/*.graphql",
  generates: {
    "app/api/v1/osograph/types/generated/types.ts": {
      plugins: ["typescript", "typescript-resolvers"],
      config: {
        enumsAsConst: true,
        contextType: "@/app/api/v1/osograph/types/context#GraphQLContext",
        scalars: {
          JSON: "Record<string, unknown>",
          DateTime: "string",
        },
        mappers: {
          DataConnection: "@/lib/types/schema-types#DataConnectionAliasRow",
          DataIngestion: "@/lib/types/schema-types#DataIngestionsRow",
          Dataset: "@/lib/types/schema-types#DatasetsRow",
          Organization: "@/lib/types/schema-types#OrganizationsRow",
          DataModel: "@/lib/types/schema-types#ModelRow",
          DataModelRevision: "@/lib/types/schema-types#ModelRevisionRow",
          DataModelRelease: "@/lib/types/schema-types#ModelReleaseRow",
          Invitation: "@/lib/types/schema-types#InvitationsRow",
          ModelContext: "@/lib/types/schema-types#ModelContextsRow",
          Notebook: "@/lib/types/schema-types#NotebooksRow",
          Run: "@/lib/types/schema-types#RunRow",
          Step: "@/lib/types/schema-types#StepRow",
          Materialization: "@/lib/types/schema-types#MaterializationRow",
          StaticModel: "@/lib/types/schema-types#StaticModelRow",
          User: "@/lib/types/schema-types#UserProfilesRow",
        },
      },
    },
    "app/api/v1/osograph/types/generated/validation.ts": {
      plugins: ["typescript-validation-schema"],
      config: {
        importFrom: "./types",
        schema: "zod",
        scalars: {
          JSON: "Record<string, unknown>",
          DateTime: "string",
        },
        scalarSchemas: {
          JSON: "z.record(z.string(), z.unknown())",
          DateTime: "z.string().datetime()",
        },
        defaultScalarSchema: "z.unknown()",
        strictScalars: true,
      },
    },
  },
};

export default config;
