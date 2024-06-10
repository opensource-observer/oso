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

{{/* 
This is copied due to some kind of error with helm and flux when overriding
portions of this
*/}}
{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "dagster.override-fullname" -}}
{{- if .Values.global.fullnameOverride -}}
{{- .Values.global.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := "dagster" -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

# Fix issues with the full name
{{- define "dagster.webserver.fullname" -}}
{{- $name := default "webserver" .Values.dagsterWebserver.nameOverride -}}
{{- $fullname := include "dagster.override-fullname" . -}}
{{- printf "%s-%s" $fullname  $name | trunc 63 | trimSuffix "-" -}}
{{- if .webserverReadOnly -}} -read-only {{- end -}}
{{- end -}}