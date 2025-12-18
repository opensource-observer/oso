export type DataIngestionFactoryType = "REST" | "GRAPHQL" | "ARCHIVE_DIR";

export interface DataIngestionConfig {
  id: string;
  datasetId: string;
  factoryType: DataIngestionFactoryType;
  config: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface CreateDataIngestionInput {
  datasetId: string;
  factoryType: DataIngestionFactoryType;
  config: Record<string, any>;
}

export interface CreateDataIngestionRunRequestInput {
  datasetId: string;
}

export interface DataIngestionRunResponse {
  success: boolean;
  message: string;
  runId: string;
}
