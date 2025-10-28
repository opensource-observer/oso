import { z } from "zod";
import { compressToEncodedURIComponent } from "lz-string";
import { logger } from "@/lib/logger";
import type {
  SaveNotebookPreviewInput,
  SaveNotebookPreviewPayload,
} from "@/lib/graphql/generated/graphql";

export type NotebookUrlOptions = {
  initialCode?: string;
  notebookId: string;
  notebookUrl: string;
  environment: Record<string, string>;
  aiPrompt?: string;
  mode: "read" | "edit";
  enablePresentMode?: boolean;
  extraFragmentParams?: Record<string, string>;
  extraQueryParams?: Record<string, string>;
  enablePostMessageStore?: boolean;
  enableDebug?: boolean;
};

const jwtResponseSchema = z.object({
  token: z.string(),
});

const previewResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
});

export function generateNotebookUrl(options: NotebookUrlOptions) {
  const {
    notebookUrl,
    notebookId,
    initialCode,
    environment,
    aiPrompt,
    enablePostMessageStore,
    enableDebug,
    mode,
    enablePresentMode = false,
    extraFragmentParams = {},
    extraQueryParams = {},
  } = options;

  const envString = compressToEncodedURIComponent(JSON.stringify(environment));
  // Generate query params
  const fragmentParams = new URLSearchParams();
  if (aiPrompt) {
    fragmentParams.append("aiPrompt", aiPrompt);
  }
  if (initialCode) {
    fragmentParams.append("code", compressToEncodedURIComponent(initialCode));
  }
  fragmentParams.append("env", envString);

  if (enablePostMessageStore) {
    fragmentParams.append("enablePostMessageStore", "true");
  }
  if (enableDebug) {
    fragmentParams.append("enableDebug", "true");
  }
  if (enablePresentMode) {
    fragmentParams.append("enablePresentMode", "true");
  }

  if (extraFragmentParams) {
    for (const [key, value] of Object.entries(extraFragmentParams)) {
      fragmentParams.append(key, value);
    }
  }
  fragmentParams.append("mode", mode);

  // Add any extra query params
  const queryParams = new URLSearchParams();
  queryParams.append("notebook", notebookId);
  if (extraQueryParams) {
    for (const [key, value] of Object.entries(extraQueryParams)) {
      queryParams.append(key, value);
    }
  }

  const fragmentParamsString = fragmentParams.toString();
  const queryParamsString = queryParams.toString();

  const fullNotebookUrl = `${notebookUrl}?${queryParamsString}#${fragmentParamsString}`;

  return fullNotebookUrl;
}

export function generatePublishedNotebookPath(
  notebookId: string,
  orgId: string,
) {
  return `${orgId}/${notebookId}.html.gz`;
}

async function fetchJwtToken(orgName: string): Promise<string> {
  logger.log(`Fetching JWT token for organization: ${orgName}`);

  const jwtResponse = await fetch(
    `/api/v1/jwt?orgName=${encodeURIComponent(orgName)}`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    },
  );

  if (!jwtResponse.ok) {
    const error = await jwtResponse.json();
    logger.error("Failed to fetch JWT token:", error?.error ?? error);
    throw new Error(`Failed to fetch JWT token: ${error?.error ?? error}`);
  }

  const jwtData = await jwtResponse.json();
  const validatedData = jwtResponseSchema.parse(jwtData);
  logger.log(`Successfully obtained JWT token for organization: ${orgName}`);

  return validatedData.token;
}

async function saveNotebookPreviewToGraphQL(
  notebookId: string,
  base64Image: string,
  token: string,
): Promise<SaveNotebookPreviewPayload> {
  logger.log(
    `Uploading notebook preview for ${notebookId}. Image size: ${base64Image.length} bytes`,
  );

  const response = await fetch("/api/v1/osograph", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      query: `
        mutation SavePreview($input: SaveNotebookPreviewInput!) {
          osoApp_saveNotebookPreview(input: $input) {
            success
            message
          }
        }
      `,
      variables: {
        input: {
          notebookId,
          previewImage: base64Image,
        } as SaveNotebookPreviewInput,
      },
    }),
  });

  const result = await response.json();

  if (result.errors) {
    logger.error("Failed to save preview:", result.errors[0].message);
    throw new Error(`Failed to save preview: ${result.errors[0].message}`);
  }

  const payload = result.data?.osoApp_saveNotebookPreview;
  if (!payload) {
    throw new Error("No response data from preview save mutation");
  }

  const validatedPayload = previewResponseSchema.parse(payload);

  if (validatedPayload.success) {
    logger.log(
      `Successfully saved notebook preview for ${notebookId} to bucket "notebook-previews"`,
    );
    logger.info("Notebook preview saved successfully");
  }

  return validatedPayload;
}

export async function saveNotebookPreview(
  notebookId: string,
  orgName: string,
  base64Image: string,
): Promise<void> {
  if (!notebookId) {
    logger.error("No notebookId provided, cannot save preview");
    return;
  }

  if (!orgName) {
    logger.error("No orgName provided, cannot save preview");
    return;
  }

  try {
    const token = await fetchJwtToken(orgName);
    await saveNotebookPreviewToGraphQL(notebookId, base64Image, token);
  } catch (error) {
    logger.error("Error saving notebook preview:", error);
    throw error;
  }
}
