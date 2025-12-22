"use client";

import * as React from "react";
import {
  useForm,
  useFormContext,
  FormProvider,
  UseFormReturn,
  useFieldArray,
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
import {
  Plus,
  Trash2,
  GripVertical,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

type PrimitiveValue = string | number | boolean | Date;
type FormDefaultValue =
  | PrimitiveValue
  | Record<string, unknown>
  | Array<unknown>
  | null
  | undefined;

interface FormSchemaFieldBase {
  label: string;
  required?: boolean;
  description?: string;
  defaultValue?: FormDefaultValue;
  placeholder?: string;
  disabled?: boolean;
  hidden?: boolean;
  advanced?: boolean;
  advancedGroup?: string;
}

interface FormSchemaStringField extends FormSchemaFieldBase {
  type: "string";
  options?: (string | { value: string; label: string })[];
}

interface FormSchemaNumberField extends FormSchemaFieldBase {
  type: "number";
}

interface FormSchemaBooleanField extends FormSchemaFieldBase {
  type: "boolean";
}

interface FormSchemaDateField extends FormSchemaFieldBase {
  type: "date";
}

interface FormSchemaObjectField extends FormSchemaFieldBase {
  type: "object";
  properties?: FormSchema;
}

interface FormSchemaArrayField extends FormSchemaFieldBase {
  type: "array";
  itemType?: "string" | "number" | "object" | "boolean" | "date";
  itemProperties?: FormSchema;
  itemOptions?: (string | { value: string; label: string })[];
}

type FormSchemaField =
  | FormSchemaStringField
  | FormSchemaNumberField
  | FormSchemaBooleanField
  | FormSchemaDateField
  | FormSchemaObjectField
  | FormSchemaArrayField;

interface FormSchema {
  [key: string]: FormSchemaField;
}

type FormBuilderZodField =
  | z.ZodString
  | z.ZodOptional<z.ZodString>
  | z.ZodNumber
  | z.ZodOptional<z.ZodNumber>
  | z.ZodObject<z.ZodRawShape>
  | z.ZodOptional<z.ZodObject<z.ZodRawShape>>
  | z.ZodBoolean
  | z.ZodOptional<z.ZodBoolean>
  | z.ZodDate
  | z.ZodOptional<z.ZodDate>
  | z.ZodArray<z.ZodTypeAny>
  | z.ZodOptional<z.ZodArray<z.ZodTypeAny>>;

const createZodSchema = (field: FormSchemaField): FormBuilderZodField => {
  const makeOptional = <T extends z.ZodTypeAny>(schema: T) =>
    field.required ? schema : schema.optional();

  switch (field.type) {
    case "string":
      return makeOptional(
        field.required
          ? z.string().min(1, { message: `${field.label} is required.` })
          : z.string(),
      );
    case "number":
      return makeOptional(
        z.number({ invalid_type_error: `${field.label} must be a number.` }),
      );
    case "boolean":
      return makeOptional(z.boolean());
    case "date":
      return makeOptional(
        z.date({ invalid_type_error: `${field.label} must be a date.` }),
      );
    case "object":
      return makeOptional(
        field.properties
          ? generateFormConfig(field.properties).zodSchema
          : z.object({}),
      );
    case "array": {
      const itemSchemas: Record<string, z.ZodTypeAny> = {
        string: z.string(),
        number: z.number(),
        boolean: z.boolean(),
        date: z.date(),
        object: field.itemProperties
          ? generateFormConfig(field.itemProperties).zodSchema
          : z.object({}),
      };
      return makeOptional(
        z.array(itemSchemas[field.itemType || "string"] ?? z.string()),
      );
    }
    default:
      throw new Error(
        `Unsupported field type: ${(field as FormSchemaField).type}`,
      );
  }
};

function generateFormConfig<T extends FormSchema>(schema: T) {
  const zodSchema: Record<string, FormBuilderZodField> = {};
  const defaultValues: Record<string, FormDefaultValue> = {};

  Object.entries(schema).forEach(([key, field]) => {
    zodSchema[key] = createZodSchema(field);

    if (field.type === "object" && field.properties) {
      const nested = generateFormConfig(field.properties);
      if (Object.keys(nested.defaultValues).length > 0) {
        defaultValues[key] = nested.defaultValues;
      }
    } else if (field.defaultValue !== undefined) {
      defaultValues[key] = field.defaultValue;
    }
  });

  const finalZodSchema = z.object(zodSchema);

  return {
    zodSchema: finalZodSchema,
    defaultValues: defaultValues as z.infer<typeof finalZodSchema>,
  };
}

interface RenderFieldProps {
  fieldName: string;
  fieldSchema: FormSchemaField;
  path: string;
  objectClassName?: string;
  horizontal?: boolean;
}

interface ArrayItemRendererProps {
  itemType: "string" | "number" | "object" | "boolean" | "date";
  itemProperties?: FormSchema;
  itemOptions?: (string | { value: string; label: string })[];
  fieldPath: string;
  fieldLabel: string;
  index: number;
  onRemove: () => void;
  onMove: (from: number, to: number) => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  disabled?: boolean;
}

interface ArrayFieldRendererProps {
  currentPath: string;
  fieldSchema: FormSchemaArrayField;
  horizontal?: boolean;
}

const ArrayFieldRenderer: React.FC<ArrayFieldRendererProps> = ({
  currentPath,
  fieldSchema,
  horizontal,
}) => {
  const { control } = useFormContext();
  const { fields, append, remove, move } = useFieldArray({
    control,
    name: currentPath,
  });

  const getDefaultValue = React.useCallback(() => {
    const typeDefaults: Record<string, unknown> = {
      number: 0,
      boolean: false,
      date: new Date(),
      string: "",
    };

    if (fieldSchema.itemType === "object" && fieldSchema.itemProperties) {
      return Object.entries(fieldSchema.itemProperties).reduce(
        (acc, [key, field]) => ({ ...acc, [key]: field.defaultValue ?? "" }),
        {},
      );
    }

    return typeDefaults[fieldSchema.itemType || "string"] ?? "";
  }, [fieldSchema.itemType, fieldSchema.itemProperties]);

  return (
    <div
      className={cn(
        "space-y-3",
        horizontal && "grid grid-cols-4 items-start gap-4",
      )}
    >
      <div
        className={cn(
          horizontal && "text-left pt-2",
          "flex items-center justify-between",
        )}
      >
        <FormLabel>
          {fieldSchema.label}
          {fieldSchema.required && (
            <span className="text-destructive ml-1">*</span>
          )}
        </FormLabel>
        {!horizontal && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 text-muted-foreground hover:text-foreground"
            onClick={() => append(getDefaultValue())}
            disabled={fieldSchema.disabled}
          >
            <Plus className="h-3.5 w-3.5" />
            <span className="text-xs">Add</span>
          </Button>
        )}
      </div>

      <div className={cn(horizontal && "col-span-3", "space-y-2")}>
        {fieldSchema.description && (
          <FormDescription className="mt-0">
            {fieldSchema.description}
          </FormDescription>
        )}

        {fields.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-6 border-2 border-dashed rounded-lg bg-muted/20">
            No items yet
          </div>
        ) : (
          <div className="space-y-2">
            {fields.map((field, index) => (
              <ArrayItemRenderer
                key={field.id}
                itemType={fieldSchema.itemType || "string"}
                itemProperties={fieldSchema.itemProperties}
                itemOptions={fieldSchema.itemOptions}
                fieldPath={`${currentPath}.${index}`}
                fieldLabel={fieldSchema.label}
                index={index}
                onRemove={() => remove(index)}
                onMove={move}
                canMoveUp={index > 0}
                canMoveDown={index < fields.length - 1}
                disabled={fieldSchema.disabled}
              />
            ))}
          </div>
        )}

        {horizontal && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full mt-2"
            onClick={() => append(getDefaultValue())}
            disabled={fieldSchema.disabled}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add {fieldSchema.label}
          </Button>
        )}

        <FormMessage />
      </div>
    </div>
  );
};

const ArrayItemRenderer: React.FC<ArrayItemRendererProps> = ({
  itemType,
  itemProperties,
  itemOptions,
  fieldPath,
  fieldLabel,
  index,
  onRemove,
  onMove,
  canMoveUp,
  canMoveDown,
  disabled,
}) => {
  const { control, getValues } = useFormContext();
  const [isCollapsed, setIsCollapsed] = React.useState(false);
  const [isDragging, setIsDragging] = React.useState(false);
  const [isDragOver, setIsDragOver] = React.useState(false);

  const getPreviewValue = React.useCallback(() => {
    const value = getValues(fieldPath);
    if (itemType === "object" && itemProperties) {
      const firstKey = Object.keys(itemProperties)[0];
      return value?.[firstKey] || `Item ${index + 1}`;
    }
    return value || `Item ${index + 1}`;
  }, [getValues, fieldPath, itemType, itemProperties, index]);

  const dragHandlers = React.useMemo(
    () => ({
      onDragStart: (e: React.DragEvent) => {
        setIsDragging(true);
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", index.toString());
      },
      onDragEnd: () => setIsDragging(false),
      onDragOver: (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        setIsDragOver(true);
      },
      onDragLeave: () => setIsDragOver(false),
      onDrop: (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        const fromIndex = parseInt(e.dataTransfer.getData("text/plain"));
        if (fromIndex !== index) onMove(fromIndex, index);
      },
    }),
    [index, onMove],
  );

  const renderItemField = () => {
    switch (itemType) {
      case "string":
        return (
          <FormField
            control={control}
            name={fieldPath}
            render={({ field }) => (
              <FormItem className="space-y-0">
                {itemOptions ? (
                  <Select
                    onValueChange={field.onChange}
                    value={field.value}
                    disabled={disabled}
                  >
                    <FormControl>
                      <SelectTrigger className="h-10">
                        <SelectValue placeholder={`Select ${fieldLabel}`} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {itemOptions.map((option) => {
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
                      {...field}
                      placeholder={`Enter ${fieldLabel}`}
                      disabled={disabled}
                      className="h-10"
                    />
                  </FormControl>
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
            name={fieldPath}
            render={({ field }) => (
              <FormItem className="space-y-0">
                <FormControl>
                  <Input
                    type="number"
                    {...field}
                    placeholder={`Enter ${fieldLabel}`}
                    disabled={disabled}
                    className="h-10"
                    onChange={(e) =>
                      field.onChange(
                        e.target.value === ""
                          ? undefined
                          : Number(e.target.value),
                      )
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        );

      case "boolean":
        return (
          <FormField
            control={control}
            name={fieldPath}
            render={({ field }) => (
              <FormItem className="flex flex-row items-center space-x-3 space-y-0 h-10">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    disabled={disabled}
                  />
                </FormControl>
                <FormLabel className="font-normal">{fieldLabel}</FormLabel>
              </FormItem>
            )}
          />
        );

      case "date":
        return (
          <FormField
            control={control}
            name={fieldPath}
            render={({ field }) => (
              <FormItem className="space-y-0">
                <FormControl>
                  <DatePicker
                    value={
                      typeof field.value === "string"
                        ? new Date(field.value)
                        : field.value
                    }
                    onChange={field.onChange}
                    disabled={disabled}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        );

      case "object":
        return itemProperties ? (
          <div className="space-y-3">
            {Object.entries(itemProperties).map(([key, fieldSchema]) => (
              <div key={key}>
                <FormLabel className="text-xs text-muted-foreground mb-1 block">
                  {fieldSchema.label}
                </FormLabel>
                <RenderField
                  fieldName={key}
                  fieldSchema={fieldSchema}
                  path={fieldPath}
                />
              </div>
            ))}
          </div>
        ) : null;

      default:
        return null;
    }
  };

  const shouldShowCollapse = itemType === "object" || !!itemProperties;
  const canDrag = !disabled && (canMoveUp || canMoveDown);

  return (
    <div
      className={cn(
        "group relative border rounded-lg bg-card transition-all duration-200",
        isDragging && "opacity-50 scale-95",
        isDragOver && "ring-2 ring-primary ring-offset-2",
        !isDragging && "hover:bg-accent/5",
      )}
      draggable={canDrag}
      {...dragHandlers}
    >
      <div className="flex items-center gap-2 p-3 border-b">
        <div className="flex items-center gap-1">
          {(canMoveUp || canMoveDown) && (
            <div
              className="h-7 w-7 flex items-center justify-center cursor-grab active:cursor-grabbing hover:bg-accent rounded"
              title="Drag to reorder"
            >
              <GripVertical className="h-4 w-4 text-muted-foreground" />
            </div>
          )}

          {shouldShowCollapse && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 hover:bg-accent"
              onClick={() => setIsCollapsed(!isCollapsed)}
              disabled={disabled}
            >
              {isCollapsed ? (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          )}
        </div>

        <div className="flex-1 min-w-0 font-medium text-sm">
          {isCollapsed ? (
            <span className="text-muted-foreground truncate block">
              {getPreviewValue()}
            </span>
          ) : (
            <span className="text-muted-foreground">Item {index + 1}</span>
          )}
        </div>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
          onClick={onRemove}
          disabled={disabled}
          title="Remove item"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      {!isCollapsed && <div className="p-4">{renderItemField()}</div>}
    </div>
  );
};

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
      const arrayFieldSchema = fieldSchema as FormSchemaArrayField;
      return (
        <ArrayFieldRenderer
          currentPath={currentPath}
          fieldSchema={arrayFieldSchema}
          horizontal={horizontal}
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
