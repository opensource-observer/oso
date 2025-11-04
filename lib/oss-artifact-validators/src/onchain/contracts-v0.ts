import { gql, GraphQLClient } from "graphql-request";
import { createPublicClient, http, PublicClient } from "viem";
import { EVMNetworkValidator } from "./evm.js";

const ANY_EVM = "ANY_EVM";
const DEFAULT_API_URL = "https://www.oso.xyz/api/v1/graphql";

export interface ContractsV0ValidatorOptions {
  apiUrl?: string;
  contractNamespace?: string;
  rpcUrl: string;
  apiKey?: string;
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
  private readonly graphqlClient: GraphQLClient;
  private readonly contractNamespace: string;
  private readonly client: PublicClient;

  constructor(options: ContractsV0ValidatorOptions) {
    const apiUrl = options.apiUrl ?? DEFAULT_API_URL;
    this.contractNamespace = options.contractNamespace ?? ANY_EVM;
    this.client = createPublicClient({
      transport: http(options.rpcUrl),
    });

    const headers: Record<string, string> = {};
    if (options.apiKey) {
      headers.Authorization = `Bearer ${options.apiKey}`;
    }
    this.graphqlClient = new GraphQLClient(apiUrl, { headers });
  }

  private normalizeAddress(address: string): `0x${string}` {
    const normalized = address.trim().toLowerCase();
    if (!normalized.startsWith("0x")) {
      throw new Error(
        `Invalid address format: ${address}. Address must start with 0x`,
      );
    }
    return normalized as `0x${string}`;
  }

  async isEOA(addr: string): Promise<boolean> {
    const normalizedAddr = this.normalizeAddress(addr);
    const code = await this.client.getCode({
      address: normalizedAddr,
    });
    return !code || code === "0x";
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

    return this.executeQuery(query, {
      contractAddress: this.normalizeAddress(addr),
    });
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

    return this.executeQuery(query, {
      factoryAddress: this.normalizeAddress(addr),
    });
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

    return this.executeQuery(query, {
      deployerAddress: this.normalizeAddress(addr),
    });
  }

  private async executeQuery(
    query: string,
    variables: Record<string, string>,
  ): Promise<boolean> {
    try {
      const response = await this.graphqlClient.request<ContractsV0Response>(
        query,
        variables,
      );

      if (this.contractNamespace === ANY_EVM) {
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
  rpcUrl: string,
  network?: string,
  apiKey?: string,
): ContractsV0Validator => {
  const contractNamespace = network ?? ANY_EVM;

  return new ContractsV0Validator({ contractNamespace, rpcUrl, apiKey });
};

export const EthereumContractsV0Validator = (
  rpcUrl: string,
  apiKey?: string,
): ContractsV0Validator =>
  createContractsV0Validator(rpcUrl, "ETHEREUM", apiKey);

export const ArbitrumContractsV0Validator = (
  rpcUrl: string,
  apiKey?: string,
): ContractsV0Validator =>
  createContractsV0Validator(rpcUrl, "ARBITRUM", apiKey);

export const BaseContractsV0Validator = (
  rpcUrl: string,
  apiKey?: string,
): ContractsV0Validator => createContractsV0Validator(rpcUrl, "BASE", apiKey);

export const OptimismContractsV0Validator = (
  rpcUrl: string,
  apiKey?: string,
): ContractsV0Validator =>
  createContractsV0Validator(rpcUrl, "OPTIMISM", apiKey);

export const AnyEVMContractsV0Validator = (
  rpcUrl: string,
  apiKey?: string,
): ContractsV0Validator => createContractsV0Validator(rpcUrl, ANY_EVM, apiKey);

export const UnichainContractsV0Validator = (
  rpcUrl: string,
  apiKey?: string,
): ContractsV0Validator =>
  createContractsV0Validator(rpcUrl, "UNICHAIN", apiKey);
