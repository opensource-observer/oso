---
sidebar_position: 5
---

# Dependencies

:::info
OSO tracks the dependency graph among projects in a collection or ecosystem. A **dependency** is a software package, module, or project that another project requires to function properly. Conversely, a **dependent** is a project that includes a specific package as its dependency. These metrics can highlight the usefulness of a given open source software project to other projects in the ecosystem.
:::

## Dependency Types

---

Dependents can be categorized as:

- **Direct Dependents**: Projects that directly include the parent package in their list of dependencies.
- **Indirect Dependents**: Projects that rely on the parent package through an intermediary package. For example, if Package A depends on Package B, and Package B relies on Package C, then Package A is an indirect dependent of Package C.

## Data Sources

---

OSO indexes software dependencies using multiple data sources:

1. **GitHub Software Bill of Materials (SBOMs)**
   - Extracted via [GitHub’s SBOM API](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exporting-a-software-bill-of-materials-for-your-repository)
   - Includes direct and indirect dependencies
   - Does not support all languages, but is largely complete for JavaScript/TypeScript, Python, Rust, and Go.
2. **Package Metadata and Historical Events**

   - Retrieved from the [deps.dev](https://deps.dev) public dataset.
   - Used to map package versions to their maintainers and track add/remove events between packages.
   - Covers major package registries (npm, PyPI, Crates.io, Go modules).
   - Includes dependency depth charts up to 10 levels deep; we typically only use the first 3 levels.

3. **Downloads from Package Registries**

   - Fetched by API from npm and from public datasets for PyPI and Crates.io.
   - Track downloads and fetch metadata from select package registries
   - Artifacts must be listed in a project's OSS Directory file in order to have these metrics indexed.

4. **OSO Public Datasets**
   - OSO provides SQL-based access to indexed dependency data in `oso_production.sboms_v0`
   - Maintainer repositories are tracked in `oso_production.package_owners_v0`

Here is a [tutorial](../../tutorials/dependencies) on how to work with OSO dependency datasets.

## Limitations

---

Dependency data is not always complete. Here are some of the limitations:

- Published packages may change maintainers, which can cause discontinuities in the dependency graph.
- Some languages are not well-supported by the data sources.
- We rely on various sources, which have different indexing and data ingestion schedules. The latest changes may not always be reflected in the OSO production data.

## Contributing

---

There is a vast amount that can be done on top of these data sources!

To contribute new metrics and models, please see our guide [here](../../contribute-models/data-models)
