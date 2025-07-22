"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { z } from "zod";
import { DYNAMIC_CONNECTOR_NAME_REGEX } from "@/lib/types/dynamic-connector";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const postgresConnectorConfigSchema = z.object({
  "connection-url": z.string().min(1, "Connection URL is required"),
  "connection-user": z.string().min(1, "Connection User is required"),
  "connection-password": z.string().min(1, "Connection Password is required"),
});

const postgresFormSchema = z.object({
  connector_name: z
    .string()
    .min(1, "Connector name is required")
    .refine(
      (val) => DYNAMIC_CONNECTOR_NAME_REGEX.test(val),
      "Invalid name, valid characters are a-z 0-9 _ -",
    ),
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
        onSubmit={() => void form.handleSubmit(onFormSubmit)}
        className="space-y-4"
      >
        <FormField
          control={form.control}
          name="connector_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Connector Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage>
                <span className="text-sm text-muted-foreground">
                  Valid characters are a-z 0-9 _ -
                  <br />
                  The organization name will be automatically added as a prefix
                </span>
              </FormMessage>
            </FormItem>
          )}
        />
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">
            Learn more about the postgres connector{" "}
            <Link
              className="text-blue-600 hover:underline"
              href="https://trino.io/docs/current/connector/postgresql.html"
              target="_blank"
            >
              here
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
