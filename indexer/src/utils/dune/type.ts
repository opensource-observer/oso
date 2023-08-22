import {
  ExecutionResponse,
  ExecutionState,
  QueryParameter,
  ResultsResponse,
} from "@cowprotocol/ts-dune-client";

// Generic dune client this will be useful for testing
export interface IDuneClient {
  refresh(
    queryId: number,
    parameters?: QueryParameter[],
    pingFrequency?: number,
  ): Promise<ResultsResponse>;
  execute(
    queryId: number,
    parameters?: QueryParameter[],
  ): Promise<ExecutionResponse>;
}

export class NoopDuneClient implements IDuneClient {
  constructor() {}

  async refresh(
    _queryId: number,
    _parameters?: QueryParameter[] | undefined,
    _pingFrequency?: number | undefined,
  ): Promise<ResultsResponse> {
    console.log("---here---");
    return {
      execution_id: "",
      state: ExecutionState.COMPLETED,
      submitted_at: new Date(),
      query_id: 123,
    };
  }

  async execute(
    _queryId: number,
    _parameters?: QueryParameter[] | undefined,
  ): Promise<ExecutionResponse> {
    return {
      execution_id: "",
      state: ExecutionState.COMPLETED,
    };
  }
}
