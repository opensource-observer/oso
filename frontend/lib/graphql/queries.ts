import { gql } from "../__generated__/gql";

const GET_ARTIFACT_BY_NAME = gql(`
  query ArtifactByName($namespace: artifact_namespace_enum!, $name: String!) {
    artifact(where: { name: { _eq: $name }, namespace: { _eq: $namespace } }) {
      id
      name
      namespace
      type
      url
    }
  }
`);

const GET_PROJECT_BY_SLUG = gql(`
  query ProjectBySlug($slug: String!) {
    project(where: { slug: { _eq: $slug } }) {
      id
      name
      slug
      verified
      description
    }
  }
`);

export { GET_ARTIFACT_BY_NAME, GET_PROJECT_BY_SLUG };
