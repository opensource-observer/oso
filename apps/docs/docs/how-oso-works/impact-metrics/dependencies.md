---
sidebar_position: 5
---

# Dependencies

:::info
OSO tracks the dependency graph among projects in a collection or ecosystem. A **dependency** is a software package, module, or project that another project requires to function properly. Conversely, a **dependent** is a project that includes a specific package as its dependency. These metrics can highlight the usefulness of a given open source software project to other projects in the ecosystem.
:::

:::warning
These metrics are currently in development.
:::

## Direct vs. Indirect Dependents

---

Dependents can be categorized as:

- **Direct Dependents**: Projects that directly include the parent package in their list of dependencies.
- **Indirect Dependents**: Projects that rely on the parent package through an intermediary package. For example, if Package A depends on Package B, and Package B relies on Package C, then Package A is an indirect dependent of Package C.

## Developer Dependencies

---

Many package managers, such as npm and Crates, distinguish between production code dependencies and **developer dependencies** that are only needed for local development and testing.

Below is an example of an npm `package.json` file with developer dependencies:

```
"name": "my_package",
"version": "1.0.0",
"dependencies": {
  "my_dep": "^1.0.0",
  "another_dep": "~2.2.0"
},
"devDependencies" : {
  "my_test_framework": "^3.1.0",
  "another_dev_dep": "1.0.0 - 1.2.0"
}
```

## Constraints on Dependency Analysis

---

For Open Source Observer, we've set the following constraints for our dependency analysis:

1. Only direct dependents are considered, excluding indirect ones.
2. Dependency analysis is restricted to specific collections or the union of specific collection sets. This ensures a more manageable indexing process and a clearer understanding of critical package relationships within an ecosystem.

Without such constraints, certain packages might appear as indirect dependents or dependencies for a vast majority of open source projects.

## Example

> Note: This is a hypothetical example. Real-world examples based on actual dependency graphs will be added soon.

Consider a collection of "Ethereum Developer Tools" with projects like `ethers` and `wagmi` and another collection called "Optimism Applications" with projects like `velodrome-finance` and `zora`. If `velodrome-finance` depends on `ethers`, and `zora` depends on both `ethers` and `wagmi`, then `ethers` has two dependents, and `wagmi` has one.

```
Ecosystems: Ethereum Developer Tools & Optimism Applications
    |
    |----> Project: ethers
    |          |
    |          |----> Dependent: velodrome-finance
    |          |----> Dependent: zora
    |
    |----> Project: wagmi
               |
               |----> Dependent: zora
```

## Dependent Metrics

---

In addition to mapping projects and their dependents, we also capture the following data about a project's dependents:

### Current Dependents

Count of dependent projects as of the most recent indexing run. These may also be referred to as "downstream dependencies" or "reverse dependencies".

### Current Dependencies

Count of dependencies as of the most recent indexing run. These may also be referred to as "upstream dependencies".

### Active Developer Dependents

Count of active developers of all dependent projects in the same collection.

### Active User Dependents

Count of active users of all dependent projects in the same collection.

### Fees Dependents

Total sequencer fees of all dependent projects in the same collection.

---

To contribute new metrics, please see our guide [here](../../contribute/impact-models)
