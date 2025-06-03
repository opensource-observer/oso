{{/*
Expand the name of the chart.
*/}}

# Disable the pgisready check due to our use of cloudsql proxy injected into the
pod.
{{- define "app.logging.config" }}
# Default log configuration for a python service. This can be
# used by uvicorn Thanks to:
# https://gist.github.com/liviaerxin/d320e33cbcddcc5df76dd92948e5be3b for a
# starting point.
version: 1
disable_existing_loggers: False
formatters:
  default:
    # "()": uvicorn.logging.DefaultFormatter
    format: '{{ .Values.app.logging.format }}'
  access:
    # "()": uvicorn.logging.AccessFormatter
    format: '{{ .Values.app.logging.format }}'
handlers:
  default:
    formatter: default
    class: logging.StreamHandler
    stream: ext://sys.stderr
  access:
    formatter: access
    class: logging.StreamHandler
    stream: ext://sys.stdout
loggers:
  uvicorn.error:
    level: {{ .Values.app.logging.uvicorn.level }}
    handlers:
      - default
    propagate: no
  uvicorn.access:
    level: {{ .Values.app.logging.uvicorn.level }}
    handlers:
      - access
    propagate: no
  {{ .Values.app.logging.appRoot.loggerName }}:
    level: {{ .Values.app.logging.appRoot.level }}
    handlers:
      - default
    propagate: no
root:
  level: {{ .Values.app.logging.root.level }}
  handlers:
    - default
  propagate: no
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
{{- define "app.fullname" -}}
{{- if .Values.global.fullnameOverride -}}
{{- .Values.global.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := "app" -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "app.labels" -}}
app.kubernetes.io/name: {{ include "app.fullname" . }}
{{- end -}}

{{- define "app.selectorLabels" -}}
{{ include "app.labels" . }}
component: {{ required "app component name is required" .Values.app.name }}
{{- end -}}