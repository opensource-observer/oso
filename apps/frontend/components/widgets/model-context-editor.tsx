"use client";

import React, { useState, useMemo } from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ColumnDef } from "@tanstack/react-table";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  safeSubmit,
} from "@/components/ui/form";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useOsoAppClient } from "@/components/hooks/oso-app";
import { toast } from "sonner";
import { logger } from "@/lib/logger";
import { DataModelColumn, ModelContext } from "@/lib/graphql/generated/graphql";
import { DataTable } from "@/components/ui/data-table";

interface ModelContextEditorProps {
  datasetId: string;
  modelId: string;
  schema: DataModelColumn[];
  existingContext?: Pick<ModelContext, "context" | "columnContext"> | null;
  className?: string;
}

const modelContextSchema = z.object({
  tableContext: z.string().optional(),
  columnContexts: z.array(
    z.object({
      name: z.string(),
      context: z.string().optional(),
    }),
  ),
});

type ModelContextFormData = z.infer<typeof modelContextSchema>;

type ColumnRow = {
  columnName: string;
  columnType: string;
  columnDescription: string | null | undefined;
  index: number;
};

function ModelContextEditor(props: ModelContextEditorProps) {
  const { datasetId, modelId, schema, existingContext, className } = props;
  const { client } = useOsoAppClient();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Filter existing column contexts to only include columns that exist in the current schema
  const filteredColumnContexts = useMemo(() => {
    if (!existingContext?.columnContext) return [];

    const schemaColumnNames = new Set(schema.map((col) => col.name));
    return existingContext.columnContext.filter((colCtx) =>
      schemaColumnNames.has(colCtx.name),
    );
  }, [existingContext, schema]);

  // Initialize form with default values
  const form = useForm<ModelContextFormData>({
    resolver: zodResolver(modelContextSchema),
    defaultValues: {
      tableContext: existingContext?.context || "",
      columnContexts: schema.map((column) => {
        const existingColContext = filteredColumnContexts.find(
          (ctx) => ctx.name === column.name,
        );
        return {
          name: column.name,
          context: existingColContext?.context || "",
        };
      }),
    },
  });

  // Prepare data for DataTable
  const tableData: ColumnRow[] = useMemo(
    () =>
      schema.map((column, index) => ({
        columnName: column.name,
        columnType: column.type,
        columnDescription: column.description,
        index,
      })),
    [schema],
  );

  // Define columns for DataTable
  const columns: ColumnDef<ColumnRow>[] = useMemo(
    () => [
      {
        accessorKey: "columnName",
        header: "Column",
        cell: ({ row }) => row.original.columnName,
      },
      {
        accessorKey: "columnType",
        header: "Type",
        cell: ({ row }) => (
          <span className="text-muted-foreground">
            {row.original.columnType}
          </span>
        ),
      },
      {
        accessorKey: "columnDescription",
        header: "Description",
        cell: ({ row }) => (
          <span className="text-muted-foreground">
            {row.original.columnDescription || "—"}
          </span>
        ),
      },
      {
        id: "context",
        header: "Context",
        cell: ({ row }) => (
          <FormField
            control={form.control}
            name={`columnContexts.${row.original.index}.context`}
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <Textarea
                    {...field}
                    placeholder="Add context..."
                    rows={1}
                    className="text-xs min-h-[64px]"
                  />
                </FormControl>
                <FormMessage className="text-xs" />
              </FormItem>
            )}
          />
        ),
      },
    ],
    [form.control],
  );

  const onSubmit = async (data: ModelContextFormData) => {
    if (!client) {
      toast.error("Client not initialized");
      return;
    }

    setIsSubmitting(true);

    try {
      // Filter out empty contexts and only include columns that exist in schema
      const schemaColumnNames = new Set(schema.map((col) => col.name));
      const columnContext = data.columnContexts
        .filter((ctx) => ctx.context && ctx.context.trim() !== "")
        .filter((ctx) => schemaColumnNames.has(ctx.name))
        .map((ctx) => ({
          name: ctx.name,
          context: ctx.context!,
        }));

      const payload = await client.updateModelContext({
        datasetId,
        modelId,
        context:
          data.tableContext && data.tableContext.trim() !== ""
            ? data.tableContext
            : null,
        columnContext: columnContext.length > 0 ? columnContext : undefined,
      });

      if (payload.success) {
        toast.success(payload.message || "Model context updated successfully");
      } else {
        toast.error(payload.message || "Failed to update model context");
      }
    } catch (error) {
      logger.error("Error updating model context:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to update model context",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Schema & Context</CardTitle>
        <CardDescription className="text-xs">
          Table schema and context to help the AI understand your model
        </CardDescription>
      </CardHeader>
      <Form {...form}>
        <form onSubmit={safeSubmit(form.handleSubmit(onSubmit))}>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="tableContext"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-sm">Table Context</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="Describe the purpose and usage of this table..."
                      rows={2}
                      className="text-sm"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-2">
              <DataTable
                columns={columns}
                data={tableData}
                pagination={false}
              />
            </div>
          </CardContent>
          <CardFooter className="pt-3">
            <Button type="submit" disabled={isSubmitting} size="sm">
              {isSubmitting ? "Saving..." : "Save"}
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>
  );
}

const ModelContextEditorMeta: CodeComponentMeta<ModelContextEditorProps> = {
  name: "ModelContextEditor",
  description: "Edit context for a model and its columns",
  props: {
    datasetId: "string",
    modelId: "string",
    schema: "object",
    existingContext: "object",
  },
};

export { ModelContextEditor, ModelContextEditorMeta };
