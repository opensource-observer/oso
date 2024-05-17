{{/*
Expand the name of the chart.
*/}}

# Disable the pgisready check due to our use of cloudsql proxy injected into the
pod.
{{- define "dagster.postgresql.pgisready" -}}
sleep 5;
{{- end }}

{{- define "dagsterYaml.postgresql.config" }}
postgres_db:
  username:
    env: DAGSTER_PG_USER
  password:
    env: DAGSTER_PG_PASSWORD
  hostname:
    env: DAGSTER_PG_HOST
  db_name:
    env: DAGSTER_PG_DB_NAME
  port:
    env: DAGSTER_PG_PORT
  params: {{- .Values.postgresql.postgresqlParams | toYaml | nindent 4 }}
  {{- if .Values.postgresql.postgresqlScheme }}
  scheme: {{ .Values.postgresql.postgresqlScheme }}
  {{- end }}
{{- end }}

# Fix issues with the full name
{{- define "dagster.webserver.fullname" -}}
{{- $name := default "webserver" .Values.dagsterWebserver.nameOverride -}}
{{- $fullname := include "dagster.fullname" . -}}
{{- printf "%s-%s" $fullname  $name | trunc 63 | trimSuffix "-" -}}
{{- if .webserverReadOnly -}} -read-only {{- end -}}
{{- end -}}