import { logger } from "@/lib/logger";
import { createAdminClient } from "@/lib/supabase/admin";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const searchParams = req.nextUrl.searchParams;
  const notebookName = searchParams.get("notebookName");
  const orgName = searchParams.get("orgName");

  if (!notebookName || !orgName) {
    return NextResponse.json(
      { error: "Missing notebookName or orgName" },
      { status: 400 },
    );
  }

  const supabaseAdmin = createAdminClient();
  const { data, error } = await supabaseAdmin
    .from("published_notebooks")
    .select(
      `
      *,
      notebooks!inner (
        notebook_name,
        organizations!inner (
          org_name
        )
      )
    `,
    )
    .eq("notebooks.notebook_name", notebookName)
    .eq("notebooks.organizations.org_name", orgName)
    .is("deleted_at", null)
    .is("notebooks.deleted_at", null)
    .single();

  if (error) {
    logger.error(error);
    return NextResponse.json(
      { error: "Failed to fetch notebook" },
      { status: 500 },
    );
  }

  if (!data) {
    return NextResponse.json({ error: "Notebook not found" }, { status: 404 });
  }

  const { notebooks: _, ...publishedNotebookData } = data;

  return NextResponse.json(publishedNotebookData);
}
