"use client";

import React, { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { PostgresConnectorForm } from "@/components/widgets/connectors/postgres-connector-form";
import { GoogleSheetsConnectorForm } from "@/components/widgets/connectors/google-sheets-connector-form";
import { ConnectorType } from "@/lib/types/dynamic-connector";
import { RegistrationProps } from "@/lib/types/plasmic";
import { cn } from "@/lib/utils";

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
  const { className, onSubmit, onCancel } = props;
  const [connectorType, setConnectorType] = useState<ConnectorType | undefined>(
    undefined,
  );

  return (
    <div className={cn(className, "space-y-6")}>
      <div className="space-y-2">
        <Label htmlFor="connector-type">Connector Type</Label>
        <Select
          value={connectorType ?? ""}
          onValueChange={(value) => setConnectorType(value as any)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a connector type" />
          </SelectTrigger>
          <SelectContent usePortal={false}>
            <SelectItem value="postgresql">PostgreSQL</SelectItem>
            <SelectItem value="gsheets">Google Sheets</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {connectorType === "postgresql" && (
        <PostgresConnectorForm onSubmit={onSubmit} onCancel={onCancel} />
      )}

      {connectorType === "gsheets" && (
        <GoogleSheetsConnectorForm onSubmit={onSubmit} onCancel={onCancel} />
      )}
    </div>
  );
}
