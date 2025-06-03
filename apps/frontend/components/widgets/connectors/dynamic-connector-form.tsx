"use client";

import React, { useState } from "react";
import {
  Select,
  MenuItem,
  Button,
  FormControl,
  InputLabel,
  Box,
  SelectChangeEvent,
  TextField,
} from "@mui/material";
import {
  PostgresConnectorConfig,
  PostgresConnectorForm,
} from "./postgres-connector-form";
import {
  GoogleSheetsConnectorConfig,
  GoogleSheetsConnectorForm,
} from "./google-sheets-connector-form";
import {
  ALLOWED_CONNECTORS,
  ConnectorType,
  DYNAMIC_CONNECTOR_NAME_REGEX,
} from "../../../lib/types/dynamic-connector";
import Link from "next/link";
import { RegistrationProps } from "../../../lib/types/plasmic";

interface BaseFormState {
  connector_name: string;
  connector_type: ConnectorType;
}

interface PostgresFormState extends BaseFormState {
  connector_type: "postgresql";
  config: PostgresConnectorConfig;
}

interface GoogleSheetsFormState extends BaseFormState {
  connector_type: "gsheets";
  config: GoogleSheetsConnectorConfig;
}

const credentialsKeys: Set<string> = new Set([
  "gsheets.credentials-key",
  "connection-password",
]);

type DynamicConnectorFormProps = {
  className?: string; // Plasmic CSS class
  onSubmit: (
    data: Record<string, any>,
    credentials: Record<string, string>,
  ) => void;
  onCancel: () => void;
};

export const DynamicConnectorFormRegistration: RegistrationProps<DynamicConnectorFormProps> =
  {
    onSubmit: {
      type: "eventHandler",
      argTypes: [
        {
          name: "data",
          type: "object",
        },
        {
          name: "credentials",
          type: "object",
        },
      ],
    },
    onCancel: {
      type: "eventHandler",
      argTypes: [],
    },
  };

export function DynamicConnectorForm(props: DynamicConnectorFormProps) {
  const { className, onSubmit, onCancel } = props; // Destructure new props
  const [formState, setFormState] = useState<
    PostgresFormState | GoogleSheetsFormState | undefined
  >();

  const handleConnectorTypeChange = (
    event: SelectChangeEvent<ConnectorType>,
  ) => {
    const newConnectorType = event.target.value as ConnectorType;
    if (newConnectorType === "postgresql") {
      setFormState({
        connector_name: formState?.connector_name ?? "",
        connector_type: "postgresql",
        config: {
          "connection-url": "",
          "connection-user": "",
          "connection-password": "",
        },
      });
    } else if (newConnectorType === "gsheets") {
      setFormState({
        connector_name: formState?.connector_name ?? "",
        connector_type: "gsheets",
        config: {
          "gsheets.credentials-key": "",
          "gsheets.metadata-sheet-id": "",
        },
      });
    } else {
      setFormState(undefined);
    }
  };

  const handleConfigChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = event.target;
    setFormState((prevFormState) => {
      if (
        prevFormState?.connector_type &&
        ALLOWED_CONNECTORS.includes(prevFormState.connector_type)
      ) {
        return {
          ...prevFormState,
          config: {
            ...prevFormState.config,
            [name]: value,
          } as any,
        };
      }
      return prevFormState; // Should ideally not be reached if connector_type is valid
    });
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (formState) {
      const credentials: Record<string, string> = {};
      const config: Record<string, string> = {};
      for (const key of Object.keys(formState.config)) {
        if (credentialsKeys.has(key)) {
          credentials[key] = (formState.config as any)[key];
        } else {
          config[key] = (formState.config as any)[key];
        }
      }
      onSubmit({ ...formState, config: config }, credentials);
    }
  };

  const handleCancel = () => {
    setFormState(undefined);
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <Box component="form" className={className} onSubmit={handleSubmit}>
      <FormControl fullWidth required>
        <InputLabel id="connector-type-label">Connector Type</InputLabel>
        <Select
          labelId="connector-type-label"
          id="connector-type-select"
          value={formState?.connector_type ?? ""}
          label="Connector Type"
          onChange={handleConnectorTypeChange}
          MenuProps={{
            disablePortal: true,
          }}
          size="small"
          fullWidth
          sx={{ mb: 2 }}
        >
          <MenuItem value="postgresql">PostgreSQL</MenuItem>
          <MenuItem value="gsheets">Google Sheets</MenuItem>
        </Select>
      </FormControl>
      {formState?.connector_type && (
        <TextField
          fullWidth
          required
          name="connector_name"
          label="Connector Name"
          error={
            !DYNAMIC_CONNECTOR_NAME_REGEX.test(formState.connector_name ?? "")
          }
          helperText={
            <span>
              Valid characters are a-z 0-9 _ -
              <br />
              The organization name will be automatically added as a prefix
            </span>
          }
          value={formState.connector_name ?? ""}
          onChange={(e) => {
            setFormState({
              ...formState,
              connector_name: e.target.value,
            });
          }}
          size="small"
        />
      )}
      {formState?.connector_type === "postgresql" && (
        <>
          <div style={{ marginBottom: "16px" }}>
            Learn more about the postgres connector{" "}
            <Link
              style={{ color: "#0000EE" }}
              href="https://trino.io/docs/current/connector/postgresql.html"
              target="_blank"
            >
              here
            </Link>
          </div>
          <PostgresConnectorForm
            formState={formState.config}
            onChange={handleConfigChange}
          />
        </>
      )}
      {formState?.connector_type === "gsheets" && (
        <>
          <div style={{ marginBottom: "16px" }}>
            Learn more about the google sheets connector{" "}
            <Link
              style={{ color: "#0000EE" }}
              href="https://trino.io/docs/current/connector/googlesheets.html"
              target="_blank"
            >
              here
            </Link>
          </div>
          <GoogleSheetsConnectorForm
            formState={formState.config}
            onChange={handleConfigChange}
          />
        </>
      )}
      <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 2 }}>
        <Button
          type="button"
          variant="outlined"
          onClick={handleCancel}
          size="small"
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={!formState}
          size="small"
        >
          Submit
        </Button>
      </Box>
    </Box>
  );
}
