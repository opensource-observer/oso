import { gzipSync } from "zlib";
import { NextRequest, NextResponse } from "next/server";
import { MARIMO_URL } from "@/lib/config";
import { withPostHogTracking } from "@/lib/clients/posthog";
import { createServerClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { logger } from "@/lib/logger";
import { getUser, signOsoJwt } from "@/lib/auth/auth";
import { tryGenerateNotebookHtml } from "@/lib/notebook/utils-server";

import { revalidateTag } from "next/cache";
import {
  generateNotebookUrl,
  generatePublishedNotebookPath,
} from "@/lib/notebook/utils";

// Next.js route control
export const maxDuration = 300;

export const POST = withPostHogTracking(async (req: NextRequest) => {
  const { notebookId } = await req.json();
  if (!notebookId || typeof notebookId !== "string") {
    return NextResponse.json(
      { error: "Invalid or missing notebookId" },
      { status: 400 },
    );
  }
  const user = await getUser(req);
  if (user.role === "anonymous") {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const supabaseClient = await createServerClient();
  const supabaseAdmin = await createAdminClient();

  const { data: notebook, error } = await supabaseClient
    .from("notebooks")
    .select("id, data, organizations!inner(id, org_name)")
    .eq("id", notebookId)
    .single();
  if (error) {
    return NextResponse.json(
      { error: "Notebook not found", details: error.message },
      { status: 404 },
    );
  }

  const osoToken = await signOsoJwt(user, {
    orgId: notebook.organizations.id,
    orgName: notebook.organizations.org_name,
  });

  const url = generateNotebookUrl({
    notebookId: notebook.id,
    notebookUrl: `${MARIMO_URL}/notebook`,
    initialCode: notebook.data ?? "",
    mode: "edit",
    environment: {
      OSO_API_KEY: osoToken,
    },
  });

  const html = await tryGenerateNotebookHtml(url);
  if (!html) {
    return NextResponse.json(
      { error: "Failed to generate notebook HTML" },
      { status: 500 },
    );
  }

  const filePath = generatePublishedNotebookPath(
    notebookId,
    notebook.organizations.id,
  );
  const compressedHtml = gzipSync(Buffer.from(html));
  const { error: uploadError } = await supabaseAdmin.storage
    .from("published-notebooks")
    .upload(filePath, compressedHtml, {
      upsert: true,
      contentType: "text/html",
      headers: {
        "Content-Encoding": "gzip",
      },
      // 5 Minute CDN cache. We will also cache on Vercel side to control it with revalidateTag
      cacheControl: "300",
    });
  if (uploadError) {
    logger.error(`Failed to upload notebook:`, uploadError);
    return NextResponse.json(
      { error: "Failed to upload notebook" },
      { status: 500 },
    );
  }
  const { data: publishedNotebook, error: upsertError } = await supabaseClient
    .from("published_notebooks")
    .upsert(
      {
        notebook_id: notebook.id,
        updated_by: user.userId,
        data_path: filePath,
        updated_at: new Date().toISOString(),
        deleted_at: null,
      },
      { onConflict: "notebook_id" },
    )
    .select("id")
    .single();
  if (upsertError) {
    logger.error(`Failed to upsert published notebook:`, upsertError);
    return NextResponse.json(
      { error: "Failed to record published notebook" },
      { status: 500 },
    );
  }

  revalidateTag(publishedNotebook.id);
  return NextResponse.json({});
});

export const DELETE = withPostHogTracking(async (req: NextRequest) => {
  const { notebookId } = await req.json();
  if (!notebookId || typeof notebookId !== "string") {
    return NextResponse.json(
      { error: "Invalid or missing notebookId" },
      { status: 400 },
    );
  }
  const user = await getUser(req);
  if (user.role === "anonymous") {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const supabaseClient = await createServerClient();
  const supabaseAdmin = await createAdminClient();

  const { data: publishedNotebook, error } = await supabaseClient
    .from("published_notebooks")
    .select("*")
    .eq("notebook_id", notebookId)
    .single();
  if (error) {
    return NextResponse.json(
      { error: "Notebook not found", details: error.message },
      { status: 404 },
    );
  }
  const { error: deleteError } = await supabaseAdmin.storage
    .from("published-notebooks")
    .remove([publishedNotebook.data_path]);
  if (deleteError) {
    return NextResponse.json(
      { error: "Failed to delete notebook file" },
      { status: 500 },
    );
  }
  const { error: updateError } = await supabaseClient
    .from("published_notebooks")
    .update({
      deleted_at: new Date().toISOString(),
      updated_by: user.userId,
    })
    .eq("id", publishedNotebook.id);
  if (updateError) {
    return NextResponse.json(
      { error: "Failed to mark notebook as deleted" },
      { status: 500 },
    );
  }
  revalidateTag(publishedNotebook.id);
  return NextResponse.json({});
});
