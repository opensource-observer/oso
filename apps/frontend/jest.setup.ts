import { SUPABASE_URL } from "@/apps/frontend/lib/config";

const setup = async (): Promise<void> => {
  // Ensure that tests are _always_ pointing to localhost or 127.0.0.1
  // Parse the SUPABASE_URL to verify
  const url = new URL(SUPABASE_URL);
  const DANGEROUS_SUPABASE_URL_TEST_WHITELIST_RAW =
    process.env.DANGEROUS_SUPABASE_URL_TEST_WHITELIST || "";
  const DANGEROUS_SUPABASE_URL_TEST_WHITELIST =
    DANGEROUS_SUPABASE_URL_TEST_WHITELIST_RAW.split(",");

  const whiteListedLocalhosts = [
    "localhost",
    "127.0.0.1",
    ...DANGEROUS_SUPABASE_URL_TEST_WHITELIST,
  ];

  // If the hostname is not in the whitelist, throw an error
  if (!whiteListedLocalhosts.includes(url.hostname)) {
    throw new Error(
      `SUPABASE_URL must point to localhost or 127.0.0.1 for tests, but got: ${SUPABASE_URL}`,
    );
  }
};

export default setup;
