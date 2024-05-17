{{/*
Expand the name of the chart.
*/}}

{{- define "dagster.postgresql.pgisready" -}}
until pg_isready -h ${DAGSTER_PG_HOST} -p ${DAGSTER_PG_PORT} -U ${DAGSTER_PG_USER}; do echo waiting for database; sleep 2; done;
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