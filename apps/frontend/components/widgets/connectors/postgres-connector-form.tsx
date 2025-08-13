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

const postgresConnectorConfigSchema = z.object({
  "connection-url": z.string().min(1, "Connection URL is required"),
  "connection-user": z.string().min(1, "Connection User is required"),
  "connection-password": z.string().min(1, "Connection Password is required"),
});

const postgresFormSchema = z.object({
  connector_name: connectorNameSchema,
  config: postgresConnectorConfigSchema,
});

type PostgresFormData = z.infer<typeof postgresFormSchema>;

interface PostgresConnectorFormProps {
  onSubmit: (
    data: Record<string, any>,
    credentials: Record<string, string>,
  ) => void;
  onCancel: () => void;
}

export function PostgresConnectorForm(props: PostgresConnectorFormProps) {
  const { onSubmit, onCancel } = props;

  const form = useForm<PostgresFormData>({
    resolver: zodResolver(postgresFormSchema),
    defaultValues: {
      connector_name: "",
      config: {
        "connection-url": "",
        "connection-user": "",
        "connection-password": "",
      },
    },
  });

  const onFormSubmit = React.useCallback(
    (data: PostgresFormData) => {
      onSubmit(
        {
          connector_name: data.connector_name,
          connector_type: "postgresql",
          config: {
            "connection-url": data.config["connection-url"].startsWith("jdbc:")
              ? data.config["connection-url"]
              : `jdbc:${data.config["connection-url"]}`,
            "connection-user": data.config["connection-user"],
          },
        },
        {
          "connection-password": data.config["connection-password"],
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
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">
            <Link
              className="text-blue-600 hover:underline inline-flex items-center gap-1"
              href="https://trino.io/docs/current/connector/postgresql.html"
              target="_blank"
            >
              View Postgresql connector documentation
            </Link>
          </div>
          <div className="space-y-4">
            <div className="space-y-2">
              <FormField
                control={form.control}
                name="config.connection-url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Connection URL</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="postgresql://host:port/database"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="space-y-2">
              <FormField
                control={form.control}
                name="config.connection-user"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>User</FormLabel>
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
                name="config.connection-password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input {...field} type="password" />
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
