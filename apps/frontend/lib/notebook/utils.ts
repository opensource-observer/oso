import { z } from "zod";
import { compressToEncodedURIComponent } from "lz-string";
import { logger } from "@/lib/logger";
import { useOsoAppClient } from "@/components/hooks/oso-app";

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
    const { client } = useOsoAppClient();
    if (!client) {
      throw new Error("OsoAppClient not initialized");
    }

    const payload = await client.saveNotebookPreview({
      notebookId,
      orgName,
      base64Image,
    });

    const validatedPayload = previewResponseSchema.parse(payload);

    if (validatedPayload.success) {
      logger.info("Notebook preview saved successfully");
    }
  } catch (error) {
    logger.error("Error saving notebook preview:", error);
    throw error;
  }
}
