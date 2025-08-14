import { gql } from "@/lib/graphql/generated/gql";

// Max TTL on Hasura is 300 seconds
// https://hasura.io/docs/latest/caching/caching-config/#controlling-cache-lifetime/

/*********************************
 * METRICS
 *********************************/

const GET_TIMESERIES_METRICS_BY_ARTIFACT = gql(`
  query TimeseriesMetricsByArtifact(
    $artifactIds: [String!],
    $metricIds: [String!],
    $startDate: Oso_Date!,
    $endDate: Oso_Date!, 
  ) {
    oso_timeseriesMetricsByArtifactV0(where: {
      artifactId: {_in: $artifactIds},
      metricId: {_in: $metricIds},
      sampleDate: { _gte: $startDate, _lte: $endDate }
    }) {
      amount
      artifactId
      metricId
      sampleDate
      unit
    }
    oso_artifactsV1(where: { artifactId: { _in: $artifactIds }}) {
      artifactId
      artifactSource
      artifactNamespace
      artifactName
    }
    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {
      metricId
      metricSource
      metricNamespace
      metricName
      displayName
      description
    }
  }
`);

const GET_TIMESERIES_METRICS_BY_PROJECT = gql(`
  query TimeseriesMetricsByProject(
    $projectIds: [String!],
    $metricIds: [String!],
    $startDate: Oso_Date!,
    $endDate: Oso_Date!, 
  ) {
    oso_timeseriesMetricsByProjectV0(where: {
      projectId: {_in: $projectIds},
      metricId: {_in: $metricIds},
      sampleDate: { _gte: $startDate, _lte: $endDate }
    }) {
      amount
      metricId
      projectId
      sampleDate
      unit
    }
    oso_projectsV1(where: { projectId: { _in: $projectIds }}) {
      projectId
      projectSource
      projectNamespace
      projectName
      displayName
      description
    }
    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {
      metricId
      metricSource
      metricNamespace
      metricName
      displayName
      description
    }
  }
`);

const GET_TIMESERIES_METRICS_BY_COLLECTION = gql(`
  query TimeseriesMetricsByCollection(
    $collectionIds: [String!],
    $metricIds: [String!],
    $startDate: Oso_Date!,
    $endDate: Oso_Date!, 
  ) {
    oso_timeseriesMetricsByCollectionV0(where: {
      collectionId: {_in: $collectionIds},
      metricId: {_in: $metricIds},
      sampleDate: { _gte: $startDate, _lte: $endDate }
    }) {
      amount
      metricId
      collectionId
      sampleDate
      unit
    }
    oso_collectionsV1(where: { collectionId: { _in: $collectionIds }}) {
      collectionId
      collectionSource
      collectionNamespace
      collectionName
      displayName
      description
    }
    oso_metricsV0(where: {metricId: {_in: $metricIds}}) {
      metricId
      metricSource
      metricNamespace
      metricName
      displayName
      description
    }
  }
`);

export {
  GET_TIMESERIES_METRICS_BY_ARTIFACT,
  GET_TIMESERIES_METRICS_BY_PROJECT,
  GET_TIMESERIES_METRICS_BY_COLLECTION,
};
