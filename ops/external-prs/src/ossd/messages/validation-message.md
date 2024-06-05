## Validation Results

{{summaryMessage}}

commit `{{sha}}`

---

{{#validationItems}}

### {{name}}

{{#messages}}

- 👉 {{.}}
  {{/messages}}

{{#errors}}

- ❌ {{.}}
  {{/errors}}

{{#warnings}}

- ⚠️ {{.}}
  {{/warnings}}

{{#successes}}

- ✅ {{.}}
  {{/successes}}

{{/validationItems}}
