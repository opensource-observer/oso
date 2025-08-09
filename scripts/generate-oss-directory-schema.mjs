// Node 20+
// Production-ready OSS Directory schema → Markdown generator for Docusaurus.
//
// Key features:
// - Robust fetch with timeout, retry, size/content-type checks
// - CLI flags: --out, --commit, --schemas, --dry-run, --repo, --branch
// - Atomic write (tmp -> rename)
// - Deterministic ordering + mini ToC + summary
// - Renders arrays as type[], unions, constraints, defaults, deprecated
// - Basic internal $ref via $defs
//
// Usage:
//   pnpm docs:gen:oss-schema
//   OSS_DIRECTORY_COMMIT=<sha> pnpm docs:gen:oss-schema
//
// Exit codes: 0 OK, 1 failure.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import https from "node:https";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------- CLI / ENV ----------
const envCommit = process.env.OSS_DIRECTORY_COMMIT || "";
const args = parseArgs(process.argv.slice(2));

const COMMIT = args.commit || envCommit || "main";
const REPO = args.repo || "opensource-observer/oss-directory";
const BRANCH = args.branch || COMMIT; // alias
const OUT_PATH = path.resolve(
  args.out ??
    path.join(__dirname, "..", "apps", "docs", "docs", "reference", "oss-directory-schema.md")
);
const DRY_RUN = Boolean(args["dry-run"]);

const SCHEMAS = (args.schemas || "project,collection")
  .split(",")
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);

// Map schema key -> {name, url}
const SCHEMA_MAP = {
  project: {
    name: "Project",
    url: () =>
      `https://raw.githubusercontent.com/${REPO}/${BRANCH}/src/resources/schema/project.json`,
  },
  collection: {
    name: "Collection",
    url: () =>
      `https://raw.githubusercontent.com/${REPO}/${BRANCH}/src/resources/schema/collection.json`,
  },
};

// ---------- Fetch (robust) ----------
function fetchWithTimeout(url, ms = 10_000, maxBytes = 2_000_000) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode} for ${url}`));
        res.resume();
        return;
      }
      const ctype = String(res.headers["content-type"] || "");
      const okType =
        ctype.startsWith("application/json") || ctype.startsWith("application/schema+json");
      if (!okType) {
        reject(new Error(`Unexpected content-type "${ctype}" for ${url}`));
        res.resume();
        return;
      }
      let size = 0;
      let data = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        size += chunk.length;
        if (size > maxBytes) {
          req.destroy(new Error(`Payload too large (> ${maxBytes} bytes) for ${url}`));
          return;
        }
        data += chunk;
      });
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on("error", reject);
    req.setTimeout(ms, () => {
      req.destroy(new Error(`Timeout after ${ms}ms for ${url}`));
    });
  });
}

async function fetchJsonWithRetry(url, attempts = 3) {
  let delay = 400;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fetchWithTimeout(url);
    } catch (e) {
      if (i === attempts - 1) throw e;
      await sleep(delay);
      delay *= 2;
    }
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ---------- Rendering helpers ----------
function jsonType(t) {
  if (Array.isArray(t)) return t.map((x) => (typeof x === "string" ? x : "object")).join(" | ");
  if (typeof t === "string") return t;
  return "object";
}

function typeString(p) {
  // Union via anyOf/oneOf/type array
  if (p?.anyOf || p?.oneOf) {
    const alts = (p.anyOf || p.oneOf).map((x) => renderSimpleType(x));
    return alts.join(" | ");
  }
  return renderSimpleType(p);
}

function renderSimpleType(p) {
  if (!p) return "object";
  if (p.type === "array") {
    const it = p.items || {};
    const base = it.type
      ? jsonType(it.type)
      : it.anyOf
      ? it.anyOf.map((x) => jsonType(x.type || "object")).join(" | ")
      : "object";
    return `${base}[]`;
  }
  if (Array.isArray(p.type))
    return p.type.map((x) => (x === "array" && p.items ? typeString(p) : x)).join(" | ");
  if (p.type) return jsonType(p.type);
  return "object";
}

function escapeMd(s = "") {
  return String(s).replace(/\|/g, "\\|").replace(/`/g, "\\`").replace(/\r?\n/g, " ");
}

function compactExample(p) {
  if (p.example !== undefined) return "`" + escapeMd(JSON.stringify(p.example)) + "`";
  if (Array.isArray(p.examples) && p.examples.length)
    return "`" + escapeMd(JSON.stringify(p.examples[0])) + "`";
  return "";
}

function enumText(p) {
  return Array.isArray(p.enum) && p.enum.length
    ? "`" + p.enum.map((v) => escapeMd(String(v))).join("`, `") + "`"
    : "";
}

function constraintsText(p = {}) {
  const parts = [];
  if ("default" in p) parts.push(`default=${fmtVal(p.default)}`);
  if (p.deprecated) parts.push("deprecated");
  if (p.format) parts.push(`format=${p.format}`);
  if (p.pattern) parts.push(`pattern=/${p.pattern}/`);
  if (p.minLength != null) parts.push(`minLength=${p.minLength}`);
  if (p.maxLength != null) parts.push(`maxLength=${p.maxLength}`);
  if (p.minimum != null) parts.push(`min=${p.minimum}`);
  if (p.maximum != null) parts.push(`max=${p.maximum}`);
  if (p.exclusiveMinimum != null) parts.push(`exclusiveMin=${p.exclusiveMinimum}`);
  if (p.exclusiveMaximum != null) parts.push(`exclusiveMax=${p.exclusiveMaximum}`);
  if (p.minItems != null) parts.push(`minItems=${p.minItems}`);
  if (p.maxItems != null) parts.push(`maxItems=${p.maxItems}`);
  if (p.uniqueItems) parts.push("uniqueItems");
  if (p.additionalProperties === false) parts.push("no additional properties");
  return parts.join("; ");
}

function fmtVal(v) {
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

// ---------- $ref resolution (internal only) ----------
function resolveRefInternal(schema, ref) {
  // Supports "#/$defs/..." or "#/definitions/..."
  if (!ref || !ref.startsWith("#/")) return null;
  const pathSegs = ref.slice(2).split("/");
  let cur = schema;
  for (const seg of pathSegs) {
    if (cur && Object.prototype.hasOwnProperty.call(cur, seg)) {
      cur = cur[seg];
    } else {
      return null;
    }
  }
  return cur || null;
}

function maybeDeref(schemaRoot, propSchema) {
  if (!propSchema) return propSchema;
  if (propSchema.$ref) {
    const target = resolveRefInternal(schemaRoot, propSchema.$ref);
    if (target)
      return {
        ...target, // base from ref target
        ...Object.fromEntries(Object.entries(propSchema).filter(([k]) => k !== "$ref")), // local overrides
      };
  }
  return propSchema;
}

// ---------- Table rendering ----------
function renderProps(schemaRoot, schema, required = []) {
  const props = schema?.properties || {};
  const keys = Object.keys(props).sort();
  const lines = [
    "| Field | Type | Required | Description | Enum / Example | Notes |",
    "|---|---|:---:|---|---|---|",
  ];
  for (const key of keys) {
    const raw = props[key] || {};
    const p = maybeDeref(schemaRoot, raw);
    const type = typeString(p);
    const req = required.includes(key) ? "✓" : "";
    const desc = escapeMd(p.description || "");
    const enumVals = enumText(p);
    const example = compactExample(p);
    const enumOrExample = enumVals || example || "—";
    const notes = constraintsText(p) || "—";
    lines.push(
      `| \`${key}\` | ${type} | ${req} | ${desc || "—"} | ${enumOrExample} | ${escapeMd(notes)} |`
    );
  }
  return lines.join("\n");
}

function anchorFromTitle(title) {
  return (
    "#" +
    title
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-")
  );
}

function renderNested(schemaRoot, schema) {
  let out = "";
  const props = schema.properties || {};
  const keys = Object.keys(props).sort();

  for (const k of keys) {
    const raw = props[k];
    const v = maybeDeref(schemaRoot, raw);

    // Object
    const isObject =
      v && ((v.type === "object" || v.properties) || (Array.isArray(v.type) && v.type.includes("object")));
    if (isObject && v.properties) {
      out += `\n\n### \`${k}\` object\n\n${renderProps(schemaRoot, v, v.required || [])}\n`;
    }

    // Array of objects
    if (v?.type === "array" && v.items) {
      const items = maybeDeref(schemaRoot, v.items);
      const itemsIsObject =
        items &&
        (items.type === "object" ||
          items.properties ||
          (Array.isArray(items.type) && items.type.includes("object")));
      if (itemsIsObject) {
        out += `\n\n### \`${k}[]\` items\n\n${renderProps(schemaRoot, items, items.required || [])}\n`;
      }
    }
  }
  return out;
}

function renderSection(title, schemaRoot) {
  const hdr = `## ${title}\n\n${schemaRoot.description || ""}\n`;
  const required = Array.isArray(schemaRoot.required) ? schemaRoot.required : [];
  const table = renderProps(schemaRoot, schemaRoot, required);
  const nested = renderNested(schemaRoot, schemaRoot);
  return `${hdr}\n${table}${nested}`;
}

// ---------- Main ----------
async function main() {
  const targets = SCHEMAS.map((key) => {
    const m = SCHEMA_MAP[key];
    if (!m) throw new Error(`Unknown schema key "${key}". Valid: ${Object.keys(SCHEMA_MAP).join(", ")}`);
    return { key, name: m.name, url: m.url() };
  });

  const fetched = [];
  for (const t of targets) {
    const json = await fetchJsonWithRetry(t.url);
    fetched.push({ ...t, schema: json });
  }

  const parts = [
    `---`,
    `id: oss-directory-schema`,
    `title: OSS Directory Schema`,
    `sidebar_label: OSS Directory Schema`,
    `description: Auto-generated reference for the OSS Directory JSON Schemas.`,
    `---`,
    ``,
    `> This page is generated. Do not edit manually. Source: \`${REPO}\` @ \`${BRANCH}\`.`,
    ``,
  ];

  // ToC
  parts.push("## Table of contents\n");
  for (const f of fetched) {
    const secTitle = `${f.name} schema`;
    parts.push(`- [${secTitle}](${anchorFromTitle(secTitle)})`);
  }
  parts.push("");

  // Sections
  for (const f of fetched) {
    parts.push(renderSection(`${f.name} schema`, f.schema));
  }

  // Summary
  const summary = fetched
    .map((f) => {
      const count = Object.keys(f.schema?.properties || {}).length;
      return `- ${f.name}: ${count} top-level fields`;
    })
    .join("\n");
  parts.push("\n---\n");
  parts.push("### Generation summary\n");
  parts.push(summary);
  parts.push("");

  const content = parts.join("\n");

  if (DRY_RUN) {
    console.log(`[dry-run] Would write ${OUT_PATH}`);
    console.log(content.slice(0, 800) + (content.length > 800 ? "\n…(truncated)…" : ""));
    return;
  }

  // Ensure folder exists + atomic write
  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  const tmp = OUT_PATH + ".tmp";
  fs.writeFileSync(tmp, content, "utf8");
  fs.renameSync(tmp, OUT_PATH);

  console.log(
    `Wrote ${path.relative(process.cwd(), OUT_PATH)} (repo=${REPO}, commit=${COMMIT})`
  );
}

// ---------- Utils ----------
function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) continue;
    const pair = a.includes("=") ? a.split("=", 2) : [a, argv[i + 1]];
    const k = pair[0];
    const v =
      pair.length === 2
        ? pair[1]
        : argv[i + 1] && !argv[i + 1].startsWith("--")
        ? argv[++i]
        : true;
    out[k.replace(/^--/, "")] = v === undefined ? true : v;
  }
  return out;
}

// ---------- Execute ----------
main().catch((e) => {
  console.error(e);
  process.exit(1);
});
