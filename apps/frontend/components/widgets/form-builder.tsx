"use client";

import * as React from "react";
import {
  useForm,
  useFormContext,
  FormProvider,
  UseFormReturn,
} from "react-hook-form";
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
import { DatePicker } from "@/components/ui/date-picker";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

interface FormSchemaField {
  type: "string" | "number" | "object" | "boolean" | "date" | "array";
  label: string;
  required?: boolean;
  description?: string;
  options?: (string | { value: string; label: string })[]; // For string type, renders a select
  properties?: FormSchema; // For object type
  itemType?: "string" | "number" | "object" | "boolean" | "date"; // For array type
  itemProperties?: FormSchema; // For array of objects
  defaultValue?: any;
  placeholder?: string;
  disabled?: boolean;
  hidden?: boolean;
  advanced?: boolean;
  advancedGroup?: string;
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
  | z.ZodOptional<z.ZodBoolean>
  | z.ZodDate
  | z.ZodOptional<z.ZodDate>
  | z.ZodArray<any>
  | z.ZodOptional<z.ZodArray<any>>;

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
      case "date": {
        const dateField = z.date({
          invalid_type_error: `${field.label} must be a date.`,
        });
        zodField = field.required ? dateField : dateField.optional();
        break;
      }
      case "object": {
        const objectField = field.properties
          ? generateFormConfig(field.properties).zodSchema
          : z.object({});
        zodField = field.required ? objectField : objectField.optional();
        break;
      }
      case "array": {
        const schemaMap: Record<string, any> = {
          string: z.string(),
          number: z.number(),
          boolean: z.boolean(),
          date: z.date(),
          object: field.itemProperties
            ? generateFormConfig(field.itemProperties).zodSchema
            : z.object({}),
        };

        const arrayItemSchema =
          schemaMap[field.itemType || "string"] ?? z.any();
        const arrayField = z.array(arrayItemSchema);
        zodField = field.required ? arrayField : arrayField.optional();
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
  horizontal?: boolean;
}

const RenderField: React.FC<RenderFieldProps> = ({
  fieldName,
  fieldSchema,
  path,
  objectClassName,
  horizontal,
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
            <FormItem
              className={cn(horizontal && "grid grid-cols-4 items-start gap-4")}
            >
              <FormLabel className={cn(horizontal && "text-left pt-2")}>
                {fieldSchema.label}
              </FormLabel>
              <div className={cn(horizontal && "col-span-3")}>
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
                      {fieldSchema.options.map((option) => {
                        const { value, label } =
                          typeof option === "string"
                            ? { value: option, label: option }
                            : option;

                        return (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        );
                      })}
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
              </div>
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
            <FormItem
              className={cn(horizontal && "grid grid-cols-4 items-start gap-4")}
            >
              <FormLabel className={cn(horizontal && "text-left pt-2")}>
                {fieldSchema.label}
              </FormLabel>
              <div className={cn(horizontal && "col-span-3")}>
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
              </div>
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

    case "date":
      return (
        <FormField
          control={control}
          name={currentPath}
          render={({ field }) => (
            <FormItem
              className={cn(horizontal && "grid grid-cols-4 items-start gap-4")}
            >
              <FormLabel className={cn(horizontal && "text-left pt-2")}>
                {fieldSchema.label}
              </FormLabel>
              <div className={cn(horizontal && "col-span-3")}>
                <FormControl>
                  <DatePicker
                    value={
                      typeof field.value === "string"
                        ? new Date(field.value)
                        : field.value
                    }
                    onChange={field.onChange}
                    disabled={fieldSchema.disabled}
                  />
                </FormControl>
                {fieldSchema.description && (
                  <FormDescription>{fieldSchema.description}</FormDescription>
                )}
                <FormMessage />
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
                objectClassName={objectClassName}
                horizontal={horizontal}
              />
            ))}
        </div>
      );

    case "array": {
      return (
        <FormField
          control={control}
          name={currentPath}
          render={({ field }) => (
            <FormItem
              className={cn(horizontal && "grid grid-cols-4 items-start gap-4")}
            >
              <FormLabel className={cn(horizontal && "text-left pt-2")}>
                {fieldSchema.label}
              </FormLabel>
              <div className={cn(horizontal && "col-span-3")}>
                <FormControl>
                  <Input
                    placeholder={fieldSchema.placeholder || "Enter JSON array"}
                    value={field.value ? JSON.stringify(field.value) : ""}
                    disabled={fieldSchema.disabled}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value);
                        field.onChange(Array.isArray(parsed) ? parsed : []);
                      } catch {
                        field.onChange(e.target.value);
                      }
                    }}
                  />
                </FormControl>
                {fieldSchema.description && (
                  <FormDescription>{fieldSchema.description}</FormDescription>
                )}
                <FormMessage />
              </div>
            </FormItem>
          )}
        />
      );
    }

    default:
      return null;
  }
};

interface FormBuilderProps {
  schema: FormSchema;
  setForm?: (form: UseFormReturn<any>) => void;
  onSubmit: (data: any) => void;
  className?: string;
  objectClassName?: string;
  footer?: React.ReactNode;
  horizontal?: boolean;
}

const FormBuilder: React.FC<FormBuilderProps> = React.forwardRef(
  function _FormBuilder(
    {
      schema = {},
      setForm,
      onSubmit,
      className,
      objectClassName,
      footer,
      horizontal,
    },
    _ref,
  ) {
    const { zodSchema, defaultValues } = React.useMemo(
      () => generateFormConfig(schema),
      [schema],
    );

    const form = useForm<z.infer<typeof zodSchema>>({
      resolver: zodResolver(zodSchema),
      defaultValues,
    });

    React.useEffect(() => {
      setForm?.(form);
    }, [form]);

    return (
      <FormProvider {...form}>
        <Form {...form}>
          <form
            onSubmit={safeSubmit(form.handleSubmit(onSubmit))}
            className={cn("space-y-6", className)}
          >
            {Object.entries(schema)
              .filter(([, field]) => !field.advanced)
              .map(([key, value]) => (
                <RenderField
                  key={key}
                  fieldName={key}
                  fieldSchema={value}
                  objectClassName={objectClassName}
                  path=""
                  horizontal={horizontal}
                />
              ))}

            {(() => {
              const advancedGroups = Object.entries(schema)
                .filter(([, field]) => field.advanced)
                .reduce<Record<string, [string, FormSchemaField][]>>(
                  (groups, entry) => {
                    const [fieldKey, field] = entry;
                    const group = field.advancedGroup ?? "Advanced";
                    groups[group] = groups[group] ?? [];
                    groups[group].push([fieldKey, field]);
                    return groups;
                  },
                  {},
                );

              if (Object.keys(advancedGroups).length === 0) {
                return null;
              }

              return (
                <Accordion
                  type="single"
                  collapsible
                  className="rounded-md border px-4"
                  defaultValue="Advanced"
                >
                  {Object.entries(advancedGroups).map(([groupName, fields]) => (
                    <AccordionItem key={groupName} value={groupName}>
                      <AccordionTrigger>{groupName}</AccordionTrigger>
                      <AccordionContent>
                        <div className="space-y-6 pt-2">
                          {fields.map(([key, value]) => (
                            <RenderField
                              key={key}
                              fieldName={key}
                              fieldSchema={value}
                              objectClassName={objectClassName}
                              path=""
                              horizontal={horizontal}
                            />
                          ))}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              );
            })()}
            {horizontal ? (
              <div className="grid grid-cols-4 items-start gap-4">
                <div className="col-start-2 col-span-3 flex justify-end">
                  {footer ?? <Button type="submit">Submit</Button>}
                </div>
              </div>
            ) : (
              (footer ?? <Button type="submit">Submit</Button>)
            )}
          </form>
        </Form>
      </FormProvider>
    );
  },
);

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
    footer: {
      type: "slot",
      hidePlaceholder: true,
    },
    onSubmit: {
      type: "eventHandler",
      argTypes: [
        {
          name: "data",
          type: "object",
        },
      ],
    },
    setForm: {
      type: "eventHandler",
      argTypes: [
        {
          name: "form",
          type: "object",
        },
      ],
      advanced: true,
    },
    horizontal: {
      type: "boolean",
      description: "Whether to display form items horizontally.",
    },
  },
  states: {
    form: {
      type: "readonly",
      onChangeProp: "setForm",
      variableType: "object",
    },
  },
};

export { FormBuilder, FormBuilderMeta };
export type { FormSchema, FormSchemaField, FormBuilderProps };
