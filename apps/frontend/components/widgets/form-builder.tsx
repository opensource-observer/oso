"use client";

import * as React from "react";
import { useForm, useFormContext, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  safeSubmit,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

interface FormSchemaField {
  type: "string" | "number" | "object" | "boolean";
  label: string;
  required?: boolean;
  description?: string;
  options?: string[]; // For string type, renders a select
  properties?: FormSchema; // For object type
  defaultValue?: any;
  placeholder?: string;
  disabled?: boolean;
  hidden?: boolean;
}

interface FormSchema {
  [key: string]: FormSchemaField;
}

type FormBuilderZodField =
  | z.ZodString
  | z.ZodOptional<z.ZodString>
  | z.ZodNumber
  | z.ZodOptional<z.ZodNumber>
  | z.ZodObject<any>
  | z.ZodOptional<z.ZodObject<any>>
  | z.ZodBoolean
  | z.ZodOptional<z.ZodBoolean>;

function generateFormConfig(schema: FormSchema): {
  zodSchema: z.ZodObject<any>;
  defaultValues: any;
} {
  const zodSchema: { [key: string]: FormBuilderZodField } = {};
  const defaultValues: { [key: string]: any } = {};

  for (const key in schema) {
    const field = schema[key];
    let zodField: FormBuilderZodField;

    if (field.type === "object" && field.properties) {
      const nestedConfig = generateFormConfig(field.properties);
      zodField = nestedConfig.zodSchema;
      if (Object.keys(nestedConfig.defaultValues).length > 0) {
        defaultValues[key] = nestedConfig.defaultValues;
      }
    } else {
      if (field.defaultValue !== undefined) {
        defaultValues[key] = field.defaultValue;
      }
    }

    switch (field.type) {
      case "string": {
        const stringField = z.string();
        zodField = field.required
          ? stringField.min(1, { message: `${field.label} is required.` })
          : stringField.optional();
        break;
      }
      case "number": {
        const numberField = z.number({
          invalid_type_error: `${field.label} must be a number.`,
        });
        zodField = field.required ? numberField : numberField.optional();
        break;
      }
      case "boolean": {
        const booleanField = z.boolean();
        zodField = field.required ? booleanField : booleanField.optional();
        break;
      }
      case "object": {
        const objectField = field.properties
          ? generateFormConfig(field.properties).zodSchema
          : z.object({});
        zodField = field.required ? objectField : objectField.optional();
        break;
      }
      default:
        throw new Error(`Unsupported field type: ${field.type}`);
    }
    zodSchema[key] = zodField;
  }

  return {
    zodSchema: z.object(zodSchema),
    defaultValues,
  };
}

interface RenderFieldProps {
  fieldName: string;
  fieldSchema: FormSchemaField;
  path: string;
  objectClassName?: string;
}

const RenderField: React.FC<RenderFieldProps> = ({
  fieldName,
  fieldSchema,
  path,
  objectClassName,
}) => {
  const { control } = useFormContext();
  const currentPath = path ? `${path}.${fieldName}` : fieldName;

  if (fieldSchema.hidden) {
    return null;
  }

  switch (fieldSchema.type) {
    case "string":
      return (
        <FormField
          control={control}
          name={currentPath}
          render={({ field }) => (
            <FormItem>
              <FormLabel>{fieldSchema.label}</FormLabel>
              {fieldSchema.options ? (
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                  disabled={fieldSchema.disabled}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder={fieldSchema.placeholder} />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {fieldSchema.options.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <FormControl>
                  <Input
                    placeholder={fieldSchema.placeholder}
                    {...field}
                    disabled={fieldSchema.disabled}
                  />
                </FormControl>
              )}
              {fieldSchema.description && (
                <FormDescription>{fieldSchema.description}</FormDescription>
              )}
              <FormMessage />
            </FormItem>
          )}
        />
      );

    case "number":
      return (
        <FormField
          control={control}
          name={currentPath}
          render={({ field }) => (
            <FormItem>
              <FormLabel>{fieldSchema.label}</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  placeholder={fieldSchema.placeholder}
                  {...field}
                  disabled={fieldSchema.disabled}
                  onChange={(e) =>
                    field.onChange(
                      e.target.value === ""
                        ? undefined
                        : Number(e.target.value),
                    )
                  }
                />
              </FormControl>
              {fieldSchema.description && (
                <FormDescription>{fieldSchema.description}</FormDescription>
              )}
              <FormMessage />
            </FormItem>
          )}
        />
      );

    case "boolean":
      return (
        <FormField
          control={control}
          name={currentPath}
          render={({ field }) => (
            <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                  disabled={fieldSchema.disabled}
                />
              </FormControl>
              <div className="space-y-1 leading-none">
                <FormLabel>{fieldSchema.label}</FormLabel>
                {fieldSchema.description && (
                  <FormDescription>{fieldSchema.description}</FormDescription>
                )}
              </div>
            </FormItem>
          )}
        />
      );

    case "object":
      return (
        <div className={cn("space-y-4 p-4 border rounded-md", objectClassName)}>
          <h3 className="font-medium">{fieldSchema.label}</h3>
          {fieldSchema.properties &&
            Object.entries(fieldSchema.properties).map(([key, value]) => (
              <RenderField
                key={key}
                fieldName={key}
                fieldSchema={value}
                path={currentPath}
              />
            ))}
        </div>
      );

    default:
      return null;
  }
};

interface FormBuilderProps {
  schema: FormSchema;
  onSubmit: (data: any) => void;
  className?: string;
  objectClassName?: string;
  footer?: React.ReactNode;
}

const FormBuilder: React.FC<FormBuilderProps> = ({
  schema,
  onSubmit,
  className,
  objectClassName,
  footer,
}) => {
  const { zodSchema, defaultValues } = React.useMemo(
    () => generateFormConfig(schema),
    [schema],
  );

  const form = useForm<z.infer<typeof zodSchema>>({
    resolver: zodResolver(zodSchema),
    defaultValues,
  });

  return (
    <FormProvider {...form}>
      <Form {...form}>
        <form
          onSubmit={safeSubmit(form.handleSubmit(onSubmit))}
          className={cn("space-y-6", className)}
        >
          {Object.entries(schema).map(([key, value]) => (
            <RenderField
              key={key}
              fieldName={key}
              fieldSchema={value}
              objectClassName={objectClassName}
              path=""
            />
          ))}
          {footer ?? <Button type="submit">Submit</Button>}
        </form>
      </Form>
    </FormProvider>
  );
};

const FormBuilderMeta: CodeComponentMeta<FormBuilderProps> = {
  name: "FormBuilder",
  description:
    "A dynamic form builder that generates a form from a JSON schema.",
  props: {
    schema: {
      type: "object",
      description: "The JSON schema to generate the form from.",
    },
    objectClassName: {
      type: "class",
    },
    footer: "slot",
    onSubmit: {
      type: "eventHandler",
      argTypes: [
        {
          name: "data",
          type: "object",
        },
      ],
    },
  },
};

export { FormBuilder, FormBuilderMeta };
export type { FormSchema, FormSchemaField, FormBuilderProps };
