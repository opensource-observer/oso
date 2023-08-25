import { notFound } from "next/navigation";
import { cachedGetProjectBySlug } from "../../../../lib/db";
import { logger } from "../../../../lib/logger";
import { catchallPathToString } from "../../../../lib/paths";

/**
 * TODO: This SSR route allows us to fetch the project from the database
 * on the first HTTP request, which should be faster than fetching it client-side
 */

type ProjectPageProps = {
  params: {
    slug: string[];
  };
};

export default async function ProjectPage(props: ProjectPageProps) {
  const { params } = props;
  const slug = catchallPathToString(params.slug);
  if (!params.slug || !Array.isArray(params.slug) || params.slug.length < 1) {
    logger.warn("Invalid project page path", params);
    notFound();
  }

  // Get project metadata from the database
  const project = await cachedGetProjectBySlug(slug);
  if (!project) {
    logger.warn(`Cannot find project (slug=${slug})`);
    notFound();
  }

  console.log(project);

  // TODO: render the Plasmic page
  return <div>My Path: {slug}</div>;
}
