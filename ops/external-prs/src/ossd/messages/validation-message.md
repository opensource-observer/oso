## Validation Results

{{summaryMessage}}

commit `{{sha}}`

---

{{#validationItems}}

### {{name}}

{{#errors}}

- ❌ {{.}}
  {{/errors}}

{{#messages}}

- 👉 {{.}}
  {{/messages}}

{{/validationItems}}
