"use client";

import React from "react";
import { TextField } from "@mui/material";

export interface GoogleSheetsConnectorConfig {
  "credentials-key": string;
  "metadata-sheet-id": string;
}

interface GoogleSheetsConnectorFormProps {
  formState: GoogleSheetsConnectorConfig;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function GoogleSheetsConnectorForm(
  props: GoogleSheetsConnectorFormProps,
) {
  const { formState, onChange } = props;

  return (
    <>
      <TextField
        fullWidth
        required
        name="credentials-key"
        label="Credentials Key (base64)"
        value={formState["credentials-key"]}
        onChange={onChange}
        size="small"
        sx={{ mb: 2 }}
      />
      <TextField
        fullWidth
        required
        name="metadata-sheet-id"
        label="Metadata Sheet ID"
        value={formState["metadata-sheet-id"]}
        onChange={onChange}
        size="small"
        placeholder="Enter Google Sheet ID"
      />
    </>
  );
}
