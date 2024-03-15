import { App } from "octokit";
import dotenv from "dotenv";

dotenv.config();

async function main() {
  const APP_TO_CHECK = process.env.APP_TO_CHECK;
  const SHA_TO_CHECK = process.env.SHA_TO_CHECK;

  const buf = Buffer.from(process.env.APP_PRIVATE_KEY!, "base64"); // Ta-da

  const app = new App({
    appId: process.env.APP_ID!,
    privateKey: buf.toString("utf-8"),
  });

  const { data } = await app.octokit.request("/app");
  console.log(`Authenticated as ${data.name}`);

  for await (const { installation } of app.eachInstallation.iterator()) {
    for await (const { octokit, repository } of app.eachRepository.iterator({
      installationId: installation.id,
    })) {
      console.log(repository.name);
      if (repository.name !== APP_TO_CHECK) {
        continue;
      }
      const resp = await octokit.request(
        "POST /repos/{owner}/{repo}/check-runs",
        {
          owner: repository.owner.login,
          repo: repository.name,
          data: {
            name: "test-deployment2",
            head_sha: SHA_TO_CHECK,
            status: "completed",
            conclusion: "success",
            output: {
              title: "test-deployment2",
              summary: "This is some summary",
            },
          },
        },
      );
      console.log(resp);
    }
  }
}

main().catch((e) => {
  console.log(e);
});
