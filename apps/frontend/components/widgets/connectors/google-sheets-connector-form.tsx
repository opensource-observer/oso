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
} from "@/components/ui/form";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import Link from "next/link";
import { DYNAMIC_CONNECTOR_NAME_REGEX } from "@/lib/types/dynamic-connector";

const googleSheetsConnectorConfigSchema = z.object({
  "credentials-key": z.string({}).min(1, "Credentials Key is required"),
  "metadata-sheet-id": z.string().min(1, "Metadata Sheet ID is required"),
});

const googleSheetsFormSchema = z.object({
  connector_name: z
    .string()
    .min(1, "Connector name is required")
    .refine(
      (val) => DYNAMIC_CONNECTOR_NAME_REGEX.test(val),
      "Invalid name, valid characters are a-z 0-9 _ -",
    ),
  config: googleSheetsConnectorConfigSchema,
});

type GoogleSheetsFormData = z.infer<typeof googleSheetsFormSchema>;

interface GoogleSheetsConnectorFormProps {
  onSubmit: (
    data: Record<string, any>,
    credentials: Record<string, string>,
  ) => void;
  onCancel: () => void;
}

export function GoogleSheetsConnectorForm(
  props: GoogleSheetsConnectorFormProps,
) {
  const { onSubmit, onCancel } = props;

  const form = useForm<GoogleSheetsFormData>({
    resolver: zodResolver(googleSheetsFormSchema),
  });

  console.log(form.getValues());

  const onFormSubmit = React.useCallback(
    (data: GoogleSheetsFormData) => {
      onSubmit(
        {
          connector_name: data.connector_name,
          connector_type: "gsheets",
          config: {
            "gsheets.metadata-sheet-id": data.config["metadata-sheet-id"],
          },
        },
        {
          "gsheets.credentials-key": btoa(data.config["credentials-key"]),
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
            Learn more about the google sheets connector{" "}
            <Link
              className="text-blue-600 hover:underline"
              href="https://trino.io/docs/current/connector/googlesheets.html"
              target="_blank"
            >
              here
            </Link>
          </div>
          <div className="space-y-4">
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
            <div className="space-y-2">
              <FormField
                control={form.control}
                name="config.metadata-sheet-id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Metadata Sheet ID</FormLabel>
                    <FormControl>
                      <Input {...field} />
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
