export type DataIngestionFactoryType = "REST" | "GRAPHQL" | "ARCHIVE2BQ";

export interface DataIngestionConfig {
  id: string;
  datasetId: string;
  factoryType: DataIngestionFactoryType;
  config: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface CreateDataIngestionConfigInput {
  datasetId: string;
  factoryType: DataIngestionFactoryType;
  config: Record<string, any>;
}

export interface CreateDataIngestionRunRequestInput {
  datasetId: string;
  configId: string;
}

export interface DataIngestionRunResponse {
  success: boolean;
  message: string;
  runId: string;
}
