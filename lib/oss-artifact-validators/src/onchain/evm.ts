import { ethers } from "ethers";

export interface AddressValidationOptions {
  osoApiKey: string;
  osoEndpoint: string;
  expectedNetwork: string; // e.g. "ARBITRUM", "BASE", "OPTIMISM", "ANY_EVM"
  rpcUrl?: string;
}

/**
 * Checks if an address is a contract using ethers.js.
 */
export async function isContractEthers(
  address: string,
  rpcUrl: string,
): Promise<boolean> {
  const provider = new ethers.JsonRpcProvider(rpcUrl);
  try {
    const code = await provider.getCode(address);
    return code !== "0x";
  } catch {
    return false;
  }
}

/**
 * Queries the contracts_v0 endpoint for contract info.
 */
export async function queryContractsV0(
  address: string,
  osoApiKey: string,
  osoEndpoint: string,
) {
  const query = `
    query ($address: String!) {
      oso_contractsV0(where: { contractAddress: { _eq: $address }, }) {
        contractAddress
        contractNamespace
        originatingAddress
        factoryAddress
      }
    }
  `;
  const response = await fetch(osoEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${osoApiKey}`,
    },
    body: JSON.stringify({
      query,
      variables: { address: address.toLowerCase() },
    }),
  });
  const data = await response.json();
  return data?.data?.oso_contractsV0 || [];
}

/**
 * Validates an address as a contract, factory, or deployer on the expected network.
 */
export async function validateAddressOnChain(
  address: string,
  options: AddressValidationOptions,
  queryFn: typeof queryContractsV0 = queryContractsV0,
): Promise<{
  isContract: boolean;
  isFactory: boolean;
  isDeployer: boolean;
  isOnExpectedNetwork: boolean;
  contractNamespaces: string[];
}> {
  const results = await queryFn(
    address,
    options.osoApiKey,
    options.osoEndpoint,
  );

  const contractNamespaces = results.map((c: any) => c.contractNamespace);
  const isContract = results.length > 0;
  const isFactory = results.some((c: any) => !!c.factoryAddress);
  const isDeployer = results.some((c: any) => !!c.originatingAddress);

  let isOnExpectedNetwork = false;
  if (options.expectedNetwork === "ANY_EVM") {
    isOnExpectedNetwork = isContract;
  } else {
    isOnExpectedNetwork = contractNamespaces.includes(options.expectedNetwork);
  }

  return {
    isContract,
    isFactory,
    isDeployer,
    isOnExpectedNetwork,
    contractNamespaces,
  };
}

/**
 * Checks if an address is an EOA
 */
export async function isEOA(address: string, rpcUrl: string): Promise<boolean> {
  return !(await isContractEthers(address, rpcUrl));
}

/**
 * Warning method for unsupported artifact types
 */
export async function warnUnsupportedArtifactType(
  addr: string,
  artifactType: string,
): Promise<boolean> {
  console.warn(
    `⚠️  ${artifactType} validation not yet implemented for address: ${addr}. Using contracts_v0 endpoint.`,
  );
  return false;
}

export async function isContractOnChain(
  address: string,
  options: AddressValidationOptions,
): Promise<boolean> {
  const query = `
    query ($address: String!) {
      oso_contractsV0(where: { contractAddress: { _eq: $address } }) {
        contractAddress
      }
    }
  `;
  const response = await fetch(options.osoEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${options.osoApiKey}`,
    },
    body: JSON.stringify({
      query,
      variables: { address: address.toLowerCase() },
    }),
  });
  const data = await response.json();
  return (data?.data?.oso_contractsV0?.length ?? 0) > 0;
}

export async function isDeployerOnChain(
  address: string,
  options: AddressValidationOptions,
): Promise<boolean> {
  const query = `
    query ($address: String!) {
      oso_contractsV0(where: { originatingAddress: { _eq: $address } }, limit: 1) {
        originatingAddress
      }
    }
  `;
  const response = await fetch(options.osoEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${options.osoApiKey}`,
    },
    body: JSON.stringify({
      query,
      variables: { address: address.toLowerCase() },
    }),
  });
  const data = await response.json();
  return (data?.data?.oso_contractsV0?.length ?? 0) > 0;
}

export async function isFactoryOnChain(
  address: string,
  options: AddressValidationOptions,
  namespace: string,
): Promise<boolean> {
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
  const response = await fetch(options.osoEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${options.osoApiKey}`,
    },
    body: JSON.stringify({
      query,
      variables: { address: address.toLowerCase(), namespace },
    }),
  });
  const data = await response.json();
  return (data?.data?.oso_contractsV0?.length ?? 0) > 0;
}
