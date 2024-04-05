// import * as duckdb from "duckdb";
// import * as fs from "fs";
// import * as path from "path";

// /**
//  * Creates two tables that are comparable via duckdb through a variety of
//  * queries. This allows us to do deeper comparative analysis of a given pull
//  * request
//  */
// class DirectoryCompare {
//   private mainDataPath: string;
//   private prDataPath: string;
//   private workPath: string;

//   constructor(workPath: string, mainDataPath: string, prDataPath: string) {
//     this.mainDataPath = mainDataPath;
//     this.prDataPath = prDataPath;
//     this.workPath = workPath;
//   }

//   // A context
//   async withComparison<T>(compareFn: (db: duckdb.Database) => Promise<T>): Promise<T> {
//     return await tmp.withDir(
//       async (t) => {
//         // Load the data
//         const main = await loadData(this.mainDataPath);
//         const pr = await loadData(this.prDataPath);
//         const db = new duckdb.Database(':memory:');

//         const tablesToCompare: { [table: string]: Project[] | Collection[] } = {
//           "main_projects": main.projects,
//           "main_collections": main.collections,
//           "pr_projects": pr.projects,
//           "pr_collections": pr.collections,
//         }

//         for (const table in tablesToCompare) {
//           // Dump the data into the work path as JSONL files
//           const dumpPath = path.resolve(path.join(t.path, `${table}.json`));
//           await this.jsonlExport(dumpPath, tablesToCompare[table]);

//           // Load that data into duckdb
//           db.run(`
//             CREATE TABLE ${table} AS
//               SELECT *
//             FROM read_json_auto('${dumpPath}');
//           `);
//         }

//         // Run the comparison
//         return await compareFn(db);
//       },
//       { unsafeCleanup: true },
//     )
//   }

//   jsonlExport<T>(path: string, arr: Array<T>): Promise<void> {
//     return new Promise((resolve, reject) => {
//       const stream = fs.createWriteStream(path, 'utf-8');
//       for (const item of arr) {
//         stream.write(JSON.stringify(item));
//         stream.write('\n');
//       }
//       stream.close((err) => {
//         if (err) {
//           return reject(err);
//         }
//         return resolve();
//       })
//     })
//   }
// }

// async function updateSummary(db: duckdb.Database) {
//   // New Collections
//   db.run()

//   // Removed Collections
//   // New Projects
//   // Removed Projects
//   // New Artifacts
//   // Removed Artifacts
//   // New Artifact Associations
//   // Removed Artifact Associations
// }
