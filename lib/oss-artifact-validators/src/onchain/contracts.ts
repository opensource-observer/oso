import { EVMNetworkValidator } from "./evm.js";

interface ContractsV0ValidatorOptions {
  osoApiKey: string;
  osoEndpoint: string;
  namespace?: string;
}

/**
 * Enhanced ContractsV0Validator using dynamic GraphQL variables
 */
export class ContractsV0Validator implements EVMNetworkValidator {
  private apiKey: string;
  private endpoint: string;
  private namespace?: string;

  constructor(opts: ContractsV0ValidatorOptions) {
    this.apiKey = opts.osoApiKey;
    this.endpoint = opts.osoEndpoint;
    this.namespace = opts.namespace;
  }

  private async queryContractsV0(query: string, variables?: any) {
    const response = await fetch(this.endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({ query, variables }),
    });

    const result = await response.json();
    return result.data;
  }

  async isEOA(addr: string): Promise<boolean> {
    const query = `
      query CheckEOA($addr: String!) {
        oso_contractsV0(where: { contractAddress: { _eq: $addr } }) {
          contractAddress
        }
      }`;
    const result = await this.queryContractsV0(query, {
      addr: addr.toLowerCase(),
    });
    return result.oso_contractsV0.length === 0;
  }

  async isContract(addr: string): Promise<boolean> {
    return !(await this.isEOA(addr));
  }

  async isFactory(addr: string): Promise<boolean> {
    const query = `
      query CheckFactory($addr: String!, $ns: String) {
        oso_contractsV0(
          where: {
            factoryAddress: { _eq: $addr },
            ${this.namespace ? "contractNamespace: { _eq: $ns }" : ""}
          },
          limit: 1
        ) {
          factoryAddress
        }
      }`;
    const variables: any = { addr: addr.toLowerCase() };
    if (this.namespace) variables.ns = this.namespace;
    const result = await this.queryContractsV0(query, variables);
    return result.oso_contractsV0.length > 0;
  }

  async isDeployer(addr: string): Promise<boolean> {
    const query = `
      query CheckDeployer($addr: String!) {
        oso_contractsV0(
          where: { originatingAddress: { _eq: $addr } },
          limit: 1
        ) {
          originatingAddress
        }
      }`;
    const result = await this.queryContractsV0(query, {
      addr: addr.toLowerCase(),
    });
    return result.oso_contractsV0.length > 0;
  }
}

export type EthereumValidatorOptions = Omit<ContractsV0ValidatorOptions, never>;
export function EthereumValidator(options: EthereumValidatorOptions) {
  return new ContractsV0Validator({ ...options });
}

export type ArbitrumValidatorOptions = Omit<ContractsV0ValidatorOptions, never>;
export function ArbitrumValidator(options: ArbitrumValidatorOptions) {
  return new ContractsV0Validator({ ...options, namespace: "ARBITRUM" });
}

export type BaseValidatorOptions = Omit<ContractsV0ValidatorOptions, never>;
export function BaseValidator(options: BaseValidatorOptions) {
  return new ContractsV0Validator({ ...options, namespace: "BASE" });
}

export type OptimismValidatorOptions = Omit<ContractsV0ValidatorOptions, never>;
export function OptimismValidator(options: OptimismValidatorOptions) {
  return new ContractsV0Validator({ ...options, namespace: "OPTIMISM" });
}
