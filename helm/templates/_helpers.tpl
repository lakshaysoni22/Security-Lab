{{/*
Expand the name of the chart.
*/}}
{{- define "LEAtTrace.name" -}}
{{- default .Chart.Name .Values.nameOverride | truncate 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "LEAtTrace.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | truncate 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | truncate 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | truncate 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}
