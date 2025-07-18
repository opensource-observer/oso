import { request, gql } from "graphql-request";
import { EVMNetworkValidator } from "./evm.js";

export interface ContractsV0ValidatorOptions {
  apiUrl?: string;
  contractNamespace?: string;
}

interface ContractsV0Response {
  oso_contractsV0: Array<{
    contractAddress: string;
    contractNamespace: string;
    deploymentDate: string;
    factoryAddress: string;
    originatingAddress: string;
    rootDeployerAddress: string;
    sortWeight: number;
  }>;
}

export class ContractsV0Validator implements EVMNetworkValidator {
  private readonly apiUrl: string;
  private readonly contractNamespace?: string;

  constructor(options: ContractsV0ValidatorOptions = {}) {
    this.apiUrl =
      options.apiUrl ?? "https://www.opensource.observer/api/v1/graphql";
    this.contractNamespace = options.contractNamespace;
  }

  async isEOA(_addr: string): Promise<boolean> {
    console.warn(
      "isEOA is not supported by contracts_v0 endpoint. Use isContract instead.",
    );
    return false;
  }

  async isContract(addr: string): Promise<boolean> {
    const query = gql`
      query ContractsV0($contractAddress: String!) {
        oso_contractsV0(where: { contractAddress: { _eq: $contractAddress } }) {
          contractAddress
          contractNamespace
        }
      }
    `;

    return this.executeQuery(query, { contractAddress: addr.toLowerCase() });
  }

  async isFactory(addr: string): Promise<boolean> {
    const query = gql`
      query ContractsV0Factory($factoryAddress: String!) {
        oso_contractsV0(where: { factoryAddress: { _eq: $factoryAddress } }) {
          factoryAddress
          contractNamespace
        }
      }
    `;

    return this.executeQuery(query, { factoryAddress: addr.toLowerCase() });
  }

  async isDeployer(addr: string): Promise<boolean> {
    const query = gql`
      query ContractsV0Deployer($deployerAddress: String!) {
        oso_contractsV0(
          where: { rootDeployerAddress: { _eq: $deployerAddress } }
        ) {
          rootDeployerAddress
          contractNamespace
        }
      }
    `;

    return this.executeQuery(query, { deployerAddress: addr.toLowerCase() });
  }

  private async executeQuery(
    query: string,
    variables: Record<string, string>,
  ): Promise<boolean> {
    try {
      const response = await request<ContractsV0Response>(
        this.apiUrl,
        query,
        variables,
      );

      if (!this.contractNamespace) {
        return response.oso_contractsV0.length > 0;
      }

      return response.oso_contractsV0.some(
        (contract) => contract.contractNamespace === this.contractNamespace,
      );
    } catch (error) {
      console.warn("Error executing query:", error);
      return false;
    }
  }
}

export const createContractsV0Validator = (
  network?: string,
): ContractsV0Validator => {
  const contractNamespace =
    network && network !== "ANY_EVM" ? network : undefined;

  return new ContractsV0Validator({ contractNamespace });
};

export const EthereumContractsV0Validator = (): ContractsV0Validator =>
  createContractsV0Validator("ETHEREUM");

export const ArbitrumContractsV0Validator = (): ContractsV0Validator =>
  createContractsV0Validator("ARBITRUM");

export const BaseContractsV0Validator = (): ContractsV0Validator =>
  createContractsV0Validator("BASE");

export const OptimismContractsV0Validator = (): ContractsV0Validator =>
  createContractsV0Validator("OPTIMISM");

export const AnyEVMContractsV0Validator = (): ContractsV0Validator =>
  createContractsV0Validator("ANY_EVM");
