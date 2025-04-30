# PyNessie GC

## Overview

PyNessie GC is a utility that removes untracked Nessie files in a Trino connector from Google Cloud Storage. This tool scans your Trino instance and compares it with the actual files in your GCS bucket, identifying and removing files that are no longer referenced by the Nessie catalog.
