// Node 20+
// Regenerates the committed snapshot pinned to a commit (env or file).

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.join(__dirname, "..");

const SNAP_DIR = path.join(repoRoot, "tests", "snapshots");
const SNAP_FILE = path.join(SNAP_DIR, "oss-directory-schema.md");
const COMMIT_FILE = path.join(SNAP_DIR, ".commit");

fs.mkdirSync(SNAP_DIR, { recursive: true });

const envCommit = process.env.OSS_DIRECTORY_COMMIT || "";
let commit =
  envCommit || (fs.existsSync(COMMIT_FILE) ? fs.readFileSync(COMMIT_FILE, "utf8").trim() : "");

if (!commit) {
  console.error("No commit provided. Set OSS_DIRECTORY_COMMIT or create tests/snapshots/.commit with a SHA.");
  process.exit(1);
}

const genPath = path.join(repoRoot, "scripts", "generate-oss-directory-schema.mjs");
const res = spawnSync(process.execPath, [genPath, "--out", SNAP_FILE, "--commit", commit], {
  cwd: repoRoot,
  stdio: "inherit",
});
if (res.status !== 0) process.exit(res.status);

if (!envCommit) {
  // Persist commit for future runs
  fs.writeFileSync(COMMIT_FILE, commit + "\n", "utf8");
}

console.log(`Updated snapshot at ${path.relative(repoRoot, SNAP_FILE)} (commit=${commit})`);
