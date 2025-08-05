import { createPublicClient, http, PublicClient } from "viem";
import { BigQuery, BigQueryOptions } from "@google-cloud/bigquery";
import _ from "lodash";

export interface EVMNetworkValidator {
  isEOA(addr: string): Promise<boolean>;
  isContract(addr: string): Promise<boolean>;
  isFactory(addr: string): Promise<boolean>;
  isDeployer(addr: string): Promise<boolean>;
}

interface GenericEVMNetworkValidatorOptions {
  rpcUrl: string;
  deployerTable: string;
  bqOptions?: BigQueryOptions;
}

/**
 * In general most EVM networks should be able to inherit directly from this.
 */
export class GenericEVMNetworkValidator implements EVMNetworkValidator {
  private client: PublicClient;
  private bq: BigQuery;
  private deployerTable: string;

  static create(
    options: GenericEVMNetworkValidatorOptions,
  ): EVMNetworkValidator {
    const client = createPublicClient({
      transport: http(options.rpcUrl),
    });
    const bq = new BigQuery(options.bqOptions);
    return new GenericEVMNetworkValidator(client, bq, options.deployerTable);
  }

  constructor(client: PublicClient, bq: BigQuery, deployerTable: string) {
    this.client = client;
    this.bq = bq;
    this.deployerTable = deployerTable;
  }

  async isEOA(addr: string): Promise<boolean> {
    const code = await this.client.getCode({
      address: addr as `0x${string}`,
    });
    return !code || code === "0x";
  }

  async isContract(addr: string): Promise<boolean> {
    return !(await this.isEOA(addr));
  }

  async isFactory(addr: string): Promise<boolean> {
    const isContract = await this.isContract(addr);
    if (!isContract) {
      return false;
    }
    return true;
  }

  async isDeployer(addr: string): Promise<boolean> {
    const query = `
    SELECT * 
    FROM ${this.deployerTable}
    WHERE LOWER(deployer_address) = '${addr}'
    `;
    const [job] = await this.bq.createQueryJob(query);
    const [results] = await job.getQueryResults();
    if (results.length !== 0) {
      return true;
    } else {
      return false;
    }
  }
}

export type EthereumOptions = Omit<
  GenericEVMNetworkValidatorOptions,
  "deployerTable"
>;

export function EthereumValidator(options: EthereumOptions) {
  return GenericEVMNetworkValidator.create(
    _.merge(options, {
      deployerTable: "`opensource-observer.oso.stg_ethereum__deployers`",
    }),
  );
}

export type ArbitrumOptions = Omit<
  GenericEVMNetworkValidatorOptions,
  "deployerTable"
>;

export function ArbitrumValidator(options: ArbitrumOptions) {
  return GenericEVMNetworkValidator.create(
    _.merge(options, {
      deployerTable: "`opensource-observer.oso.stg_arbitrum__deployers`",
    }),
  );
}

export type BaseOptions = Omit<
  GenericEVMNetworkValidatorOptions,
  "deployerTable"
>;

export function BaseValidator(options: BaseOptions) {
  return GenericEVMNetworkValidator.create(
    _.merge(options, {
      deployerTable: "`opensource-observer.oso.stg_base__deployers`",
    }),
  );
}

export type OptimismOptions = Omit<
  GenericEVMNetworkValidatorOptions,
  "deployerTable"
>;

export function OptimismValidator(options: OptimismOptions) {
  return GenericEVMNetworkValidator.create(
    _.merge(options, {
      deployerTable: "`opensource-observer.oso.stg_optimism__deployers`",
    }),
  );
}
