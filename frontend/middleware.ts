import { NextResponse } from "next/server";
import { NextRequest } from "next/server";
import { supabaseQuery } from "./lib/supabase-client";
import { catchallPathToString, pathToNamespaceEnum } from "./lib/paths";

/**
 * Rewrites for `/project/:slug`
 * @param request
 * @param slug
 * @returns
 */
async function projectMiddleware(request: NextRequest, slug: string) {
  // Get project metadata from the database
  const projects = await supabaseQuery({
    tableName: "Project",
    columns: "id,slug",
    filters: [["slug", "eq", slug]],
  });
  if (!projects || projects.length < 1) {
    console.warn(`Cannot find project (slug=${slug})`);
    return NextResponse.next();
  }

  // Get the project
  const project = projects[0];
  //console.log(project);
  return NextResponse.rewrite(
    new URL(`/projectById/${project.id}`, request.url),
  );
}

/**
 * Rewrites for `/artifact/:namespace/:name`
 * @param request
 * @param namespace
 * @param name
 * @returns
 */
async function artifactMiddleware(
  request: NextRequest,
  namespace: string,
  name: string,
) {
  // Get artifact metadata from the database
  const artifacts = await supabaseQuery({
    tableName: "Artifact",
    columns: "id,namespace,name",
    filters: [
      ["namespace", "eq", namespace],
      ["name", "eq", name],
    ],
  });
  if (!artifacts || artifacts.length < 1) {
    console.warn(`Cannot find artifact (namespace=${namespace}, name=${name})`);
    return NextResponse.next();
  }

  // Get the project
  const artifact = artifacts[0];
  //console.log(artifact);
  return NextResponse.rewrite(
    new URL(`/artifactById/${artifact.id}`, request.url),
  );
}

/**
 * Route depending on whether the path starts with `/project` or `/artifact`
 * @param request
 * @returns
 */
export async function middleware(request: NextRequest) {
  const pathParts = request.nextUrl.pathname.split("/").filter((x) => !!x);
  if (pathParts.length > 1 && pathParts[0] === "project") {
    return projectMiddleware(request, catchallPathToString(pathParts.slice(1)));
  } else if (pathParts.length > 2 && pathParts[0] === "artifact") {
    const namespaceEnum = pathToNamespaceEnum(pathParts[1]);
    if (namespaceEnum) {
      return artifactMiddleware(
        request,
        namespaceEnum,
        catchallPathToString(pathParts.slice(2)),
      );
    }
  }
  console.warn("Invalid path: ", pathParts);
  return NextResponse.next();
}

export const config = {
  matcher: ["/artifact/:path+", "/project/:path+"],
};
