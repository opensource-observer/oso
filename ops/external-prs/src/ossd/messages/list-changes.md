This pull request includes the following changes for commit `{{sha}}`:

|                      | Unchanged                           | Added                            | Removed                            | Updated                |
| -------------------- | ----------------------------------- | -------------------------------- | ---------------------------------- | ---------------------- |
| Projects             | {{ projects.unchanged }}            | {{ projects.added }}             | {{projects.removed}}               | {{ projects.updated }} |
| Blockchain Artifacts | {{ artifacts.blockchain.existing }} | {{ artifacts.blockchain.added }} | {{ artifacts.blockchain.removed }} | N/A                    |
| Code Artifacts       | {{ artifacts.code.existing }}       | {{ artifacts.code.added }}       | {{ artifacts.code.removed }}       | N/A                    |
| Package Artifacts    | {{ artifacts.package.existing }}    | {{ artifacts.package.added }}    | {{ artifacts.package.removed}}     | N/A                    |

Please note:

- The code artifacts have yet to be expanded to include any repositories if the
  url's given are organizations.
- The blockchain artifacts have yet to be validated

Validation will occur once an `oss-directory` contributor with write access
triggers this pull request for validation.
