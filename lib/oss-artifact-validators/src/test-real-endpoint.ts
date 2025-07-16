import { ContractsV0Provider } from "./providers/contracts-v0.js";
import * as dotenv from "dotenv";

dotenv.config();

async function testRealEndpoint() {
  const apiKey = process.env.OSO_API_KEY;
  if (!apiKey) {
    console.error("OSO_API_KEY environment variable not set");
    process.exit(1);
  }

  const provider = new ContractsV0Provider({
    osoApiKey: apiKey,
    osoEndpoint: "https://www.opensource.observer/api/v1/graphql",
    timeout: 20000,
  });

  const testAddress = "0x8f7dab4508d792416a1c4911464613299642952a";

  console.log(`Testing contracts_v0 endpoint with address: ${testAddress}`);
  console.log("=".repeat(60));

  try {
    console.log("\n1. Testing basic address lookup...");
    const lookup = await provider.lookup(testAddress);
    console.log("Lookup result:", JSON.stringify(lookup, null, 2));

    console.log("\n2. Testing contract summary...");
    const summary = await provider.contractSummary(testAddress);
    console.log("Contract summary:", JSON.stringify(summary, null, 2));

    console.log("\n3. Testing deployer check...");
    const isDeployer = await provider.isDeployerOnChain(
      testAddress,
      "ARBITRUM",
    );
    console.log("Is deployer:", isDeployer);

    console.log("\n4. Testing factory check...");
    const isFactory = await provider.isFactoryOnChain(testAddress, "ARBITRUM");
    console.log("Is factory:", isFactory);
  } catch (error) {
    console.error("Error testing endpoint:", error);
    process.exit(1);
  }
}

testRealEndpoint();
