"use client";

import React from "react";
import { TextField } from "@mui/material";

export interface PostgresConnectorConfig {
  "connection-url": string;
  "connection-user": string;
  "connection-password": string;
}
interface PostgresConnectorFormProps {
  formState: PostgresConnectorConfig;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function PostgresConnectorForm(props: PostgresConnectorFormProps) {
  const { formState, onChange } = props;

  return (
    <>
      <TextField
        fullWidth
        required
        name="connection-url"
        label="Connection URL"
        value={formState["connection-url"]}
        onChange={onChange}
        placeholder="jdbc:postgresql://host:port/database"
        size="small"
        sx={{ mb: 2 }}
      />
      <TextField
        fullWidth
        required
        name="connection-user"
        label="Connection User"
        value={formState["connection-user"]}
        onChange={onChange}
        size="small"
        sx={{ mb: 2 }}
      />
      <TextField
        fullWidth
        required
        name="connection-password"
        label="Connection Password"
        type="password"
        value={formState["connection-password"]}
        onChange={onChange}
        size="small"
      />
    </>
  );
}
