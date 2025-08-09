// Node 20+
// Compares freshly generated output vs committed snapshot, pinned to a commit.
// Exit codes: 0 match, 1 mismatch/error.

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

// Resolve commit SHA: env overrides file
const envCommit = process.env.OSS_DIRECTORY_COMMIT || "";
const fileCommit = fs.existsSync(COMMIT_FILE) ? fs.readFileSync(COMMIT_FILE, "utf8").trim() : "";
const COMMIT = (envCommit || fileCommit || "").trim();

if (!COMMIT) {
  console.error("Snapshot test requires a pinned commit. Set OSS_DIRECTORY_COMMIT env or tests/snapshots/.commit");
  process.exit(1);
}
if (!fs.existsSync(SNAP_FILE)) {
  console.error(`Snapshot missing at ${path.relative(repoRoot, SNAP_FILE)}. Run: pnpm test:schema:update`);
  process.exit(1);
}

// Generate to a temp path
const tmpOut = path.join(SNAP_DIR, "oss-directory-schema.actual.tmp.md");
const genPath = path.join(repoRoot, "scripts", "generate-oss-directory-schema.mjs");

const res = spawnSync(process.execPath, [genPath, "--out", tmpOut, "--commit", COMMIT], {
  cwd: repoRoot,
  stdio: ["ignore", "pipe", "pipe"],
  encoding: "utf8",
});
if (res.status !== 0) {
  console.error("Generator failed:\n" + (res.stderr || res.stdout));
  process.exit(1);
}

const expected = fs.readFileSync(SNAP_FILE, "utf8");
const actual = fs.readFileSync(tmpOut, "utf8");

if (expected === actual) {
  fs.unlinkSync(tmpOut);
  console.log("Schema snapshot: OK");
  process.exit(0);
}

// Simple diff: show first differing line
const expLines = expected.split(/\r?\n/);
const actLines = actual.split(/\r?\n/);
let idx = 0;
while (idx < expLines.length && idx < actLines.length && expLines[idx] === actLines[idx]) idx++;

console.error("Schema snapshot: MISMATCH");
console.error(`First difference at line ${idx + 1}`);
console.error("--- expected");
console.error(expLines.slice(Math.max(0, idx - 3), idx + 3).join("\n"));
console.error("+++ actual");
console.error(actLines.slice(Math.max(0, idx - 3), idx + 3).join("\n"));
console.error(`\nTo update snapshot (after intentional changes): pnpm test:schema:update`);
process.exit(1);
