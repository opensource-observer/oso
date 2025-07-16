import {
  AddressLookupProvider,
  AddressLookupSummary,
  ContractLookupProvider,
  ContractLookupSummary,
} from "../common/interfaces.js";

export interface ContractsV0Config {
  osoApiKey: string;
  osoEndpoint: string;
  timeout?: number;
}

export interface ContractsV0Response {
  contractAddress: string;
  contractNamespace: string;
  originatingAddress?: string;
  factoryAddress?: string;
}

/**
 * Provider that uses the contracts_v0 endpoint to lookup address and contract information
 */
export class ContractsV0Provider
  implements AddressLookupProvider, ContractLookupProvider
{
  constructor(private config: ContractsV0Config) {}

  async lookup(address: string): Promise<AddressLookupSummary> {
    const contracts = await this.queryContracts(address);
    const namespaces = contracts.map((c) => c.contractNamespace);

    return {
      address: address.toLowerCase(),
      isContract: contracts.length > 0,
      exists: contracts.length > 0,
      namespaces,
    };
  }

  async contractSummary(address: string): Promise<ContractLookupSummary> {
    const contracts = await this.queryContracts(address);
    const namespaces = contracts.map((c) => c.contractNamespace);

    return {
      address: address.toLowerCase(),
      isContract: contracts.length > 0,
      exists: contracts.length > 0,
      namespaces,
      isFactory: contracts.some((c) => !!c.factoryAddress),
      isDeployer: contracts.some((c) => !!c.originatingAddress),
    };
  }

  async isDeployerOnChain(address: string, _chain: string): Promise<boolean> {
    const query = `
      query ($address: String!) {
        oso_contractsV0(where: { originatingAddress: { _eq: $address } }, limit: 1) {
          originatingAddress
        }
      }
    `;
    const data = await this.executeQuery(query, {
      address: address.toLowerCase(),
    });
    return (data?.data?.oso_contractsV0?.length ?? 0) > 0;
  }

  async isFactoryOnChain(address: string, chain: string): Promise<boolean> {
    const query = `
      query ($address: String!, $namespace: String!) {
        oso_contractsV0(
          where: { factoryAddress: { _eq: $address }, contractNamespace: { _eq: $namespace } }
          limit: 1
        ) {
          factoryAddress
        }
      }
    `;
    const data = await this.executeQuery(query, {
      address: address.toLowerCase(),
      namespace: chain,
    });
    return (data?.data?.oso_contractsV0?.length ?? 0) > 0;
  }

  private async queryContracts(
    address: string,
  ): Promise<ContractsV0Response[]> {
    const query = `
      query ($address: String!) {
        oso_contractsV0(where: { contractAddress: { _eq: $address } }) {
          contractAddress
          contractNamespace
          originatingAddress
          factoryAddress
        }
      }
    `;
    const data = await this.executeQuery(query, {
      address: address.toLowerCase(),
    });
    return data?.data?.oso_contractsV0 || [];
  }

  private async executeQuery(
    query: string,
    variables: Record<string, any>,
  ): Promise<any> {
    const timeout = this.config.timeout || 15000; // Default 15 seconds

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(this.config.osoEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.config.osoApiKey}`,
        },
        body: JSON.stringify({
          query,
          variables,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === "AbortError") {
          throw new Error(`Request timeout after ${timeout}ms`);
        }
        throw new Error(`Contracts v0 API request failed: ${error.message}`);
      }

      throw new Error("Unknown error occurred during contracts v0 API request");
    }
  }
}
