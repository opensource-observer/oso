import type { Metadata } from "next";
import { createServerClient } from "@/lib/supabase/server";
import { ogImageInfoSchema } from "@/lib/types/og-image";
import { DOMAIN } from "@/lib/config";
import { logger } from "@/lib/logger";

export async function generateNotebookMetadata(
  orgName: string,
  notebookName: string,
): Promise<Metadata | null> {
  try {
    const supabase = await createServerClient();

    const { data, error } = await supabase.rpc("get_og_image_info", {
      p_org_name: orgName,
      p_notebook_name: notebookName,
    });

    if (error) return null;

    const validation = ogImageInfoSchema.safeParse(data);
    if (!validation.success) return null;

    const paramFields = [
      ["org", orgName],
      ["notebook", notebookName],
      ["avatar", validation.data.authorAvatar],
      ["description", validation.data.description],
    ].filter(([, v]) => v !== null) as [string, string][];

    const PROTOCOL = DOMAIN.includes("localhost") ? "http:" : "https:";
    const ogImageUrl = new URL("/api/v1/og", `${PROTOCOL}//${DOMAIN}`);

    for (const [key, value] of paramFields) {
      ogImageUrl.searchParams.set(key, value);
    }

    const title = `${orgName}/${notebookName}`;
    const description =
      validation.data.description ||
      "Interactive data analysis and visualization";

    return {
      title,
      description,
      openGraph: {
        title,
        description,
        type: "website",
        images: [ogImageUrl.toString()],
      },
      twitter: {
        card: "summary_large_image",
        title,
        description,
        images: [ogImageUrl.toString()],
      },
    };
  } catch (error) {
    logger.error("Error generating notebook metadata:", error);
    return null;
  }
}
