export { }
// import { Command } from "commander";
// import {
//   AirbyteConfig,
//   AirbyteLogger,
//   AirbyteSourceBase,
//   AirbyteSourceRunner,
//   AirbyteSpec,
//   AirbyteStreamBase,
// } from "faros-airbyte-cdk";
// import spec from "./resources/spec.json" assert { type: "json" };
// import VError from "verror";
// import { Repositories } from "./streams/index.js";
// import { GraphQLClient } from "graphql-request";

// function graphQLClient(
//   token: string,
//   graphQLApiUrl: string = "https://api.github.com/graphql",
// ) {
//   return new GraphQLClient(graphQLApiUrl, {
//     headers: {
//       authorization: `Bearer ${token}`,
//     },
//   });
// }

// interface GithubResolveReposConfig extends AirbyteConfig {
//   readonly github_token: string;
//   readonly urls: string[];
// }

// /** The main entry point. */
// export function mainCommand(): Command {
//   const logger = new AirbyteLogger();
//   const source = new GithubResolveReposSource(logger);
//   return new AirbyteSourceRunner(logger, source).mainCommand();
// }

// /** Example source implementation. */
// export class GithubResolveReposSource extends AirbyteSourceBase<GithubResolveReposConfig> {
//   async spec(): Promise<AirbyteSpec> {
//     // eslint-disable-next-line @typescript-eslint/no-var-requires
//     return new AirbyteSpec(spec);
//   }
//   async checkConnection(
//     config: GithubResolveReposConfig,
//   ): Promise<[boolean, VError | undefined]> {
//     if (config.github_token) {
//       return [true, undefined];
//     }
//     return [false, new VError("Github Token is required")];
//   }

//   streams(config: GithubResolveReposConfig): AirbyteStreamBase[] {
//     return [
//       new Repositories(
//         graphQLClient(config.github_token),
//         config.urls,
//         this.logger,
//       ),
//     ];
//   }
// }

// mainCommand().parse();
