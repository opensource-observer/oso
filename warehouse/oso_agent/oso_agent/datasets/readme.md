### Eval Dataset README

_Standard operating guide for authoring, maintaining, and running evaluation datasets across **any** agent_

---

## 1. Authoring new evals

| Step  | Action                        | Details                                                                                                                  |
| ----- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **1** | _Draft the NL ↔ answer pair_ | Write the natural-language **question** and the **ground-truth answer** (SQL, JSON, etc)                                 |
| **2** | _Pick metadata_               | `priority` (P0-P2), `difficulty` (easy/medium/hard), **one or more** `question_categories`, etc                          |
| **3** | _Call the helper_             | Add a `create_text2sql_example( … )` (or the equivalent helper for your dataset) inside the correct `datasets/*.py` file |
| **4** | _Run `pnpm pyright` & Commit_ | Type checker guarantees: (a) category is legal, (b) query-type inference passes, (c) table-prefix rule (`oso.`) holds    |

---

## 2. Question backlog

`BacklogQuestion` is a lightweight store for ideas that are **not** production-grade yet.

| Field                              | Purpose                                                               |
| ---------------------------------- | --------------------------------------------------------------------- |
| `question`                         | Required NL question.                                                 |
| `real_user_question`               | Signals external vs internal idea.                                    |
| `answer` _(optional)_              | Draft answer if someone already started.                              |
| `additional metadata` _(optional)_ | You can store helpful insights for what the eval's categories will be |
| `notes`                            | Free-form reasoning, blockers, TODOs.                                 |

**Workflow**

- backlog → pick one → refine answer & metadata → promote to `Example` → delete from backlog.

---

## 3 · Extending / changing the schemas

### 3.1 Modify an **existing** schema

1. Open `types/datasets.py`, locate the relevant `pydantic` class, and edit the field list or types as needed.
   - Where practical, prefer `Literal[...]` enums so values stay well-defined.
2. Update the matching `create_…()` helper so it builds objects that follow the revised class.
3. Touch every dataset file (`datasets/*.py`) that still calls the helper and add or remove parameters so each example matches the new signature.
4. Run **`pnpm pyright`** – no type errors means you caught every usage.

### 3.2 Add a **new** schema

1. In `types/datasets.py` create a new `pydantic` model that **at minimum** re-uses `ExampleInput`, `ExampleOutput`, and includes `real_user_question: bool` (required).
2. Define supportive enums (`Literal[…]`) for any constrained fields.
3. Write a `create_<your_dataset>()` helper that returns the new class.
4. In `datasets/`, add a `<your_dataset>.py` file that imports the helper and populates an `ExampleList`.
5. If the dataset will be uploaded to Phoenix, ensure the list variable you export is named `ExampleList` (the uploader in `datasets/uploader.py` expects that).

### 3.3 Misc rules

- **Always** prefix real SQL tables with `oso.` – it keeps queries consistent and drives `determine_sql_models_used()`.
- Once the schema or data changes, re-run **pyright**; CI must be green before merge.

---
