import { ValidationErrors } from "@/app/api/v1/osograph/utils/errors";
import { DatasetType } from "@/lib/types/dataset";

export function validateTableId(tableId: string) {
  const tableIdHasValidPrefix =
    tableId.startsWith("data_model_") ||
    tableId.startsWith("data_ingestion_") ||
    tableId.startsWith("data_connection_") ||
    tableId.startsWith("static_model_");
  if (!tableIdHasValidPrefix) {
    throw ValidationErrors.invalidInput(
      "tableId",
      "tableId must start with one of the following prefixes: data_model_, data_ingestion_, data_connection_, static_model_",
    );
  }
}

export function generateTableId(datasetType: DatasetType, modelId: string) {
  switch (datasetType) {
    case "USER_MODEL":
      return `data_model_${modelId}`;
    case "STATIC_MODEL":
      return `static_model_${modelId}`;
    case "DATA_INGESTION":
      return `data_ingestion_${modelId}`;
    case "DATA_CONNECTION":
      return `data_connection_${modelId}`;
    default:
      throw ValidationErrors.invalidInput(
        "datasetType",
        `Unsupported dataset type: ${datasetType}`,
      );
  }
}
