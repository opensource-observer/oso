import { Repo } from "./github.js";
import { App } from "octokit";

export interface BaseArgs {
  githubAppPrivateKey: string;
  githubAppId: string;
  repo: Repo;
  app: App;
}
