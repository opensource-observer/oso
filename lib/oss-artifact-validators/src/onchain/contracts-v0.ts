import { gql, request } from "graphql-request";
import { Web3 } from "web3";
import { EVMNetworkValidator } from "./evm.js";

const ANY_EVM = "ANY_EVM";
const DEFAULT_API_URL = "https://www.opensource.observer/api/v1/graphql";

export interface ContractsV0ValidatorOptions {
  apiUrl?: string;
  contractNamespace?: string;
  rpcUrl: string;
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
  private readonly contractNamespace: string;
  private readonly web3: Web3;

  constructor(options: ContractsV0ValidatorOptions) {
    this.apiUrl = options.apiUrl ?? DEFAULT_API_URL;
    this.contractNamespace = options.contractNamespace ?? ANY_EVM;
    this.web3 = new Web3(options.rpcUrl);
  }

  private normalizeAddress(address: string): string {
    return address.trim().toLowerCase();
  }

  async isEOA(addr: string): Promise<boolean> {
    const normalizedAddr = this.normalizeAddress(addr);
    const code = await this.web3.eth.getCode(normalizedAddr);
    return code === "0x";
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
      const response = await request<ContractsV0Response>(
        this.apiUrl,
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
): ContractsV0Validator => {
  const contractNamespace = network ?? ANY_EVM;

  return new ContractsV0Validator({ contractNamespace, rpcUrl });
};

export const EthereumContractsV0Validator = (
  rpcUrl: string,
): ContractsV0Validator => createContractsV0Validator(rpcUrl, "ETHEREUM");

export const ArbitrumContractsV0Validator = (
  rpcUrl: string,
): ContractsV0Validator => createContractsV0Validator(rpcUrl, "ARBITRUM");

export const BaseContractsV0Validator = (
  rpcUrl: string,
): ContractsV0Validator => createContractsV0Validator(rpcUrl, "BASE");

export const OptimismContractsV0Validator = (
  rpcUrl: string,
): ContractsV0Validator => createContractsV0Validator(rpcUrl, "OPTIMISM");

export const AnyEVMContractsV0Validator = (
  rpcUrl: string,
): ContractsV0Validator => createContractsV0Validator(rpcUrl, ANY_EVM);
