import { ethers } from "ethers";
import {
  AddressLookupProvider,
  AddressLookupSummary,
} from "../common/interfaces.js";

export interface RpcConfig {
  rpcUrl: string;
}

/**
 * Provider that uses RPC calls to check if an address is a contract
 */
export class RpcProvider implements AddressLookupProvider {
  private provider: ethers.JsonRpcProvider;

  constructor(private config: RpcConfig) {
    this.provider = new ethers.JsonRpcProvider(config.rpcUrl);
  }

  async lookup(address: string): Promise<AddressLookupSummary> {
    try {
      const code = await this.provider.getCode(address);
      const isContract = code !== "0x";

      return {
        address: address.toLowerCase(),
        isContract,
        exists: true, // If we can check it, it exists on chain
        namespaces: [], // RPC doesn't provide namespace information
      };
    } catch {
      return {
        address: address.toLowerCase(),
        isContract: false,
        exists: false,
        namespaces: [],
      };
    }
  }
}
