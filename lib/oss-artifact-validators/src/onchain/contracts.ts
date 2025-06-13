import { EVMNetworkValidator } from "./evm.js";

export type ArtifactType = 'CONTRACT' | 'FACTORY' | 'DEPLOYER' | 'EOA' | 'WALLET' | 'SAFE' | 'BRIDGE';

interface ContractResponse {
  contractNamespace: string;
  originatingAddress: string;
  rootDeployerAddress: string;
  deploymentDate: string;
}

export class ContractsValidator {
  private apiKey: string;
  private endpoint: string;
  private network: string;

  constructor(network: string, apiKey: string, endpoint: string = 'https://www.opensource.observer/api/v1/graphql') {
    this.network = network;
    this.apiKey = apiKey;
    this.endpoint = endpoint;

    if (!apiKey) {
      console.warn('Warning: No API key provided. Requests may fail.');
    }
  }

  private async queryContracts(address: string): Promise<ContractResponse[]> {
    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': this.apiKey
      },
      body: JSON.stringify({
        query: `
          query Oso_contractsV0 {
            oso_contractsV0(
              where: {
                contractAddress: {
                  _eq: "${address.toLowerCase()}"
                }
              }
            ) {
              contractNamespace
              originatingAddress
              rootDeployerAddress
              deploymentDate
            }
          }
        `,
        variables: {}
      })
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const data = await response.json();
    if (data.errors) {
      throw new Error(data.errors[0].message);
    }

    return data.data.oso_contractsV0;
  }

  async validateAddress(address: string) {
    try {
      const contracts = await this.queryContracts(address);
      
      if (!contracts || contracts.length === 0) {
        return {
          isValid: false,
          artifactType: 'CONTRACT',
          warnings: ['No contracts found for this address'],
          networks: []
        };
      }

      const networks = contracts.map((c: ContractResponse) => c.contractNamespace);
      const isAnyEVM = this.network === 'ANY_EVM';
      const isValid = isAnyEVM || networks.includes(this.network);

      return {
        isValid,
        artifactType: 'CONTRACT',
        networks,
        deploymentCount: contracts.length
      };
    } catch (error) {
      return {
        isValid: false,
        artifactType: 'CONTRACT',
        warnings: [error instanceof Error ? error.message : 'Unknown error occurred'],
        networks: []
      };
    }
  }

  async isContract(address: string): Promise<boolean> {
    try {
      const contracts = await this.queryContracts(address);
      return contracts && contracts.length > 0;
    } catch (error) {
      console.log(`error in validating contract addr:`, error)
      return false;
    }
  }

  async isFactory(address: string): Promise<boolean> {
    try {
      const contracts = await this.queryContracts(address);
      return contracts && contracts.length > 0;
    } catch (error) {
      console.log(`error in validating factory addr:`, error)
      return false;
    }
  }

  async isDeployer(address: string): Promise<boolean> {
    try {
      const contracts = await this.queryContracts(address);
      return contracts && contracts.length > 0;
    } catch (error) {
      console.log(`error in validating deployer addr:`, error)
      return false;
    }
  }

  async isEOA(address: string): Promise<boolean> {
    try {
      const contracts = await this.queryContracts(address);
      return !contracts || contracts.length === 0;
    } catch (error) {
      console.log(`error in validating EOA addr:`, error)
      return false;
    }
  }
}

// Network-specific validators
export function EthereumValidator(apiKey?: string): EVMNetworkValidator {
  return new ContractsValidator('ethereum', apiKey ?? '');
}

export function ArbitrumValidator(apiKey?: string): EVMNetworkValidator {
  return new ContractsValidator('arbitrum', apiKey ?? '');
}

export function BaseValidator(apiKey?: string): EVMNetworkValidator {
  return new ContractsValidator('base', apiKey ?? '');
}

export function OptimismValidator(apiKey?: string): EVMNetworkValidator {
  return new ContractsValidator('optimism', apiKey ?? '');
} 