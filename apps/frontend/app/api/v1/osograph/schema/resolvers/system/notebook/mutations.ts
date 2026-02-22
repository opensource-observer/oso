import { getSystemClient } from "@/app/api/v1/osograph/utils/access-control";
import type { GraphQLContext } from "@/app/api/v1/osograph/types/context";
import {
  ResourceErrors,
  ServerErrors,
} from "@/app/api/v1/osograph/utils/errors";
import { GraphQLResolverModule } from "@/app/api/v1/osograph/types/utils";
import {
  SavePublishedNotebookHtmlSchema,
  validateInput,
} from "@/app/api/v1/osograph/utils/validation";
import { generatePublishedNotebookPath } from "@/lib/notebook/utils";
import { revalidateTag } from "next/cache";
import { MutationSavePublishedNotebookHtmlArgs } from "@/lib/graphql/generated/graphql";

export const notebookPublishingResolvers: GraphQLResolverModule<GraphQLContext> =
  {
    Mutation: {
      savePublishedNotebookHtml: async (
        _: unknown,
        args: MutationSavePublishedNotebookHtmlArgs,
        context: GraphQLContext,
      ) => {
        const client = getSystemClient(context);

        const { notebookId, htmlContent } = validateInput(
          SavePublishedNotebookHtmlSchema,
          args.input,
        );

        console.log("Encoded", htmlContent);

        // Decode base64 content
        const byteArray = Buffer.from(htmlContent, "base64");

        const { data: notebook } = await client
          .from("notebooks")
          .select("org_id")
          .eq("id", notebookId)
          .single();
        if (!notebook) {
          throw ResourceErrors.notFound(`Notebook ${notebookId} not found`);
        }

        const filePath = generatePublishedNotebookPath(
          notebookId,
          notebook.org_id,
        );
        // Save the HTML content to Supabase Storage
        const { data: uploadData, error: uploadError } = await client.storage
          .from("published-notebooks")
          .upload(filePath, byteArray, {
            upsert: true,
            contentType: "text/html",
            headers: {
              "Content-Encoding": "gzip",
            },
            // 5 Minute CDN cache. We will also cache on Vercel side to control it with revalidateTag
            cacheControl: "300",
          });
        if (uploadError || !uploadData) {
          throw ServerErrors.internal(
            `Failed to upload published notebook HTML for notebook ${notebookId}: ${uploadError.message}`,
          );
        }

        // Update the published_notebooks table with the new data path
        const { data: publishedNotebook, error: upsertError } = await client
          .from("published_notebooks")
          .upsert(
            {
              notebook_id: notebookId,
              data_path: filePath,
              updated_at: new Date().toISOString(),
              deleted_at: null,
            },
            { onConflict: "notebook_id" },
          )
          .select("id")
          .single();

        if (upsertError || !publishedNotebook) {
          throw ServerErrors.internal(
            `Failed to update published_notebooks for notebook ${notebookId}: ${upsertError.message}`,
          );
        }

        revalidateTag(publishedNotebook.id);

        return {
          message: "Saved published notebook HTML",
          success: true,
        };
      },
    },
  };
