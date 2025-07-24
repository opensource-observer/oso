"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  safeSubmit,
} from "@/components/ui/form";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  ConnectorNameField,
  connectorNameSchema,
} from "@/components/widgets/connectors/connector-form-utils";
import { Textarea } from "@/components/ui/textarea";

const bigQueryConnectorConfigSchema = z.object({
  "project-id": z.string().min(1, "Project ID is required"),
  "credentials-key": z.string().min(1, "Connection User is required"),
});

const bigQueryFormSchema = z.object({
  connector_name: connectorNameSchema,
  config: bigQueryConnectorConfigSchema,
});

type BigQueryFormData = z.infer<typeof bigQueryFormSchema>;

interface BigQueryConnectorFormProps {
  onSubmit: (
    data: Record<string, any>,
    credentials: Record<string, string>,
  ) => void;
  onCancel: () => void;
}

export function BigQueryConnectorForm(props: BigQueryConnectorFormProps) {
  const { onSubmit, onCancel } = props;

  const form = useForm<BigQueryFormData>({
    resolver: zodResolver(bigQueryFormSchema),
    defaultValues: {
      connector_name: "",
      config: {
        "project-id": "",
        "credentials-key": "",
      },
    },
  });

  const onFormSubmit = React.useCallback(
    (data: BigQueryFormData) => {
      onSubmit(
        {
          connector_name: data.connector_name,
          connector_type: "bigquery",
          config: {
            "bigquery.project-id": data.config["project-id"],
          },
        },
        {
          "bigquery.credentials-key": btoa(
            data.config["credentials-key"].trim(),
          ),
        },
      );
    },
    [onSubmit],
  );

  return (
    <Form {...form}>
      <form
        onSubmit={safeSubmit(form.handleSubmit(onFormSubmit))}
        className="space-y-4"
      >
        <ConnectorNameField control={form.control} />
        <div className="space-y-4 text-sm text-muted-foreground">
          Only service account JSON keys are supported.
          <br />
          For private datasets, ensure the service account has the{" "}
          <code className="bg-muted px-1 py-0.5 rounded">
            BigQuery Data Viewer
          </code>{" "}
          role.
          <Link
            className="text-blue-600 hover:underline inline-flex items-center gap-1"
            href="https://trino.io/docs/current/connector/bigquery.html"
            target="_blank"
          >
            View BigQuery connector documentation
          </Link>
          <div className="space-y-4">
            <div className="space-y-2">
              <FormField
                control={form.control}
                name="config.project-id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Project ID</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="space-y-2">
              <FormField
                control={form.control}
                name="config.credentials-key"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>JSON Credentials</FormLabel>
                    <FormControl>
                      <Textarea {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              size="sm"
              disabled={form.formState.isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={form.formState.isSubmitting}
            >
              Submit
            </Button>
          </div>
        </div>
      </form>
    </Form>
  );
}
