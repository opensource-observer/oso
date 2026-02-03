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
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  Plus,
  Trash2,
  GripVertical,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { FormErrorBanner } from "@/components/widgets/form-error-banner";

type PrimitiveValue = string | number | boolean | Date;
type FormDefaultValue =
  | PrimitiveValue
  | Record<string, unknown>
  | Array<unknown>
  | null
  | undefined;

const getTypeDefault = (fieldType: string): unknown => {
  const typeDefaults: Record<string, unknown> = {
    number: undefined,
    date: undefined,
    string: "",
    boolean: false,
    array: [],
    object: {},
    union: undefined,
  };
  return typeDefaults[fieldType] ?? "";
};

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
  skipIfEmpty?: boolean;
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
  allowDynamicKeys?: boolean;
}

interface FormSchemaArrayField extends FormSchemaFieldBase {
  type: "array";
  itemType?: "string" | "number" | "object" | "boolean" | "date";
  itemProperties?: FormSchema;
  itemOptions?: (string | { value: string; label: string })[];
}

interface FormSchemaUnionVariant {
  value: string;
  label: string;
  properties?: FormSchema;
}

interface FormSchemaUnionField extends FormSchemaFieldBase {
  type: "union";
  variants: FormSchemaUnionVariant[];
  discriminator?: string;
  variantSelector?: "dropdown" | "tabs" | "radio";
  collapseNested?: boolean;
  nullable?: boolean;
}

type FormSchemaField =
  | FormSchemaStringField
  | FormSchemaNumberField
  | FormSchemaBooleanField
  | FormSchemaDateField
  | FormSchemaObjectField
  | FormSchemaArrayField
  | FormSchemaUnionField;

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
  | z.ZodOptional<z.ZodArray<z.ZodTypeAny>>
  | z.ZodUnion<[z.ZodTypeAny, z.ZodTypeAny, ...z.ZodTypeAny[]]>
  | z.ZodOptional<z.ZodUnion<[z.ZodTypeAny, z.ZodTypeAny, ...z.ZodTypeAny[]]>>
  | z.ZodDiscriminatedUnion<string, z.ZodDiscriminatedUnionOption<string>[]>
  | z.ZodOptional<
      z.ZodDiscriminatedUnion<string, z.ZodDiscriminatedUnionOption<string>[]>
    >
  | z.ZodNullable<z.ZodTypeAny>
  | z.ZodEffects<any, any>;

function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === "string") return value.trim() === "";
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === "object" && value !== null) {
    return Object.values(value).every((v) => isEmpty(v));
  }
  return false;
}

function stripUndefinedDeep<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map(stripUndefinedDeep).filter((v) => v !== undefined) as T;
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .map(([k, v]) => [k, stripUndefinedDeep(v)])
        .filter(([, v]) => v !== undefined),
    ) as T;
  }

  return value;
}

function applySkipIfEmpty<T extends z.ZodTypeAny>(
  schema: T,
  shouldSkip: boolean,
): T | z.ZodEffects<T, z.output<T> | undefined, z.input<T>> {
  if (!shouldSkip) return schema;
  return schema.transform((val) => (isEmpty(val) ? undefined : val));
}

function createZodUnion(
  schemas: z.ZodTypeAny[],
): z.ZodUnion<[z.ZodTypeAny, z.ZodTypeAny, ...z.ZodTypeAny[]]> {
  if (schemas.length < 2) {
    throw new Error("Union requires at least 2 schemas");
  }
  const [first, second, ...rest] = schemas;
  return z.union([first, second, ...rest] as [
    z.ZodTypeAny,
    z.ZodTypeAny,
    ...z.ZodTypeAny[],
  ]);
}

function createDiscriminatedUnion(
  discriminator: string,
  schemas: z.ZodObject<z.ZodRawShape>[],
): z.ZodDiscriminatedUnion<
  string,
  [
    z.ZodObject<z.ZodRawShape>,
    z.ZodObject<z.ZodRawShape>,
    ...z.ZodObject<z.ZodRawShape>[],
  ]
> {
  if (schemas.length < 2) {
    throw new Error("Discriminated union requires at least 2 schemas");
  }
  const [first, second, ...rest] = schemas;
  return z.discriminatedUnion(discriminator, [first, second, ...rest] as [
    z.ZodObject<z.ZodRawShape>,
    z.ZodObject<z.ZodRawShape>,
    ...z.ZodObject<z.ZodRawShape>[],
  ]);
}

const createZodSchema = (field: FormSchemaField): FormBuilderZodField => {
  const makeOptional = <T extends z.ZodTypeAny>(schema: T) =>
    field.required ? schema : schema.optional();

  const getBaseSchema = (): z.ZodTypeAny => {
    switch (field.type) {
      case "string":
        return field.required
          ? z.string().min(1, { message: `${field.label} is required.` })
          : z.string();
      case "number": {
        const baseSchema = z.number({
          invalid_type_error: `${field.label} must be a number.`,
        });
        const withOptional = field.required
          ? baseSchema
          : baseSchema.optional();
        return z.preprocess((val) => {
          if (
            field.skipIfEmpty &&
            (val === "" || val === null || val === undefined)
          ) {
            return undefined;
          }
          return Number.isNaN(val) ? undefined : val;
        }, withOptional);
      }
      case "boolean":
        return z.boolean();
      case "date":
        return z.date({ invalid_type_error: `${field.label} must be a date.` });
      case "object":
        if (field.properties) {
          return generateFormConfig(field.properties).zodSchema;
        } else if (field.allowDynamicKeys) {
          return z
            .array(
              z.object({
                key: z.string().min(1, "Key cannot be empty"),
                value: z.string(),
              }),
            )
            .refine(
              (pairs) => {
                const keys = pairs.map((p) => p.key);
                return keys.length === new Set(keys).size;
              },
              { message: "Duplicate keys are not allowed" },
            )
            .transform((pairs) => {
              return pairs.reduce(
                (acc, pair) => {
                  acc[pair.key] = pair.value;
                  return acc;
                },
                {} as Record<string, string>,
              );
            });
        }
        return z.object({});
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
        return z.array(itemSchemas[field.itemType || "string"] ?? z.string());
      }
      case "union": {
        const unionField = field as FormSchemaUnionField;

        if (unionField.variants.length === 0) {
          return z.never();
        }

        if (unionField.variants.length === 1) {
          const variant = unionField.variants[0];
          if (!variant.properties) {
            const literalSchema = z.literal(variant.value);
            const withNullable: z.ZodTypeAny = unionField.nullable
              ? literalSchema.nullable()
              : literalSchema;
            return makeOptional(withNullable);
          }
          const singleSchema = generateFormConfig(variant.properties).zodSchema;
          const withNullable = unionField.nullable
            ? singleSchema.nullable()
            : singleSchema;
          return makeOptional(withNullable);
        }

        const variantSchemas = unionField.variants.map((variant) => {
          if (!variant.properties) {
            return z.literal(variant.value);
          }
          const schema = generateFormConfig(variant.properties).zodSchema;
          return unionField.discriminator ? schema : schema.strict();
        });

        const canUseDiscriminatedUnion =
          unionField.discriminator &&
          variantSchemas.length >= 2 &&
          !unionField.nullable &&
          unionField.required;

        let unionSchema: z.ZodTypeAny;

        if (canUseDiscriminatedUnion) {
          const allAreObjects = variantSchemas.every(
            (schema) => schema instanceof z.ZodObject,
          );

          if (allAreObjects) {
            unionSchema = createDiscriminatedUnion(
              unionField.discriminator!,
              variantSchemas as z.ZodObject<z.ZodRawShape>[],
            );
          } else {
            unionSchema = createZodUnion(variantSchemas);
          }
        } else {
          unionSchema = createZodUnion(variantSchemas);
        }

        if (unionField.nullable) {
          unionSchema = unionSchema.nullable();
        }

        return unionField.required ? unionSchema : unionSchema.optional();
      }
      default:
        throw new Error(
          `Unsupported field type: ${(field as FormSchemaField).type}`,
        );
    }
  };

  const optionalWrapped = makeOptional(getBaseSchema());
  return applySkipIfEmpty(optionalWrapped, field.skipIfEmpty ?? false);
};

function normalizeDefaultValues(
  values: Record<string, unknown>,
  properties: FormSchema,
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => {
      const fieldSchema = properties[key];

      if (value === undefined) {
        if (!fieldSchema) return [key, ""];

        switch (fieldSchema.type) {
          case "string":
            return [key, ""];
          case "number":
            return [key, undefined];
          case "boolean":
            return [key, false];
          case "date":
            return [key, undefined];
          case "array":
            return [key, []];
          case "object":
            return [key, fieldSchema.allowDynamicKeys ? [] : {}];
          case "union":
            return [key, undefined];
          default:
            return [key, ""];
        }
      }

      if (
        fieldSchema?.type === "object" &&
        fieldSchema.allowDynamicKeys &&
        value &&
        typeof value === "object" &&
        !Array.isArray(value)
      ) {
        return [
          key,
          Object.entries(value).map(([k, v]) => ({
            key: k,
            value: String(v),
          })),
        ];
      }

      if (
        fieldSchema?.type === "object" &&
        fieldSchema.properties &&
        value &&
        typeof value === "object" &&
        !Array.isArray(value)
      ) {
        return [
          key,
          normalizeDefaultValues(
            value as Record<string, unknown>,
            fieldSchema.properties,
          ),
        ];
      }

      if (fieldSchema?.type === "array" && Array.isArray(value)) {
        if (value.length === 0) {
          return [key, []];
        }

        const arrayField = fieldSchema as FormSchemaArrayField;

        if (arrayField.itemType === "object" && arrayField.itemProperties) {
          return [
            key,
            value.map((item) => {
              if (typeof item === "object" && item !== null) {
                return normalizeDefaultValues(
                  item as Record<string, unknown>,
                  arrayField.itemProperties!,
                );
              }
              return item;
            }),
          ];
        }

        return [key, value];
      }

      if (
        fieldSchema?.type === "union" &&
        value &&
        typeof value === "object" &&
        !Array.isArray(value)
      ) {
        const unionField = fieldSchema as FormSchemaUnionField;
        const valueObj = value as Record<string, unknown>;

        let matchingVariant: FormSchemaUnionVariant | null = null;

        if (unionField.discriminator) {
          const discriminatorValue = valueObj[unionField.discriminator];
          matchingVariant =
            unionField.variants.find((v) => v.value === discriminatorValue) ||
            null;
        } else {
          let bestMatchScore = 0;
          let bestMatchVariant: FormSchemaUnionVariant | null = null;

          for (const variant of unionField.variants) {
            if (!variant.properties) continue;
            const variantKeys = Object.keys(variant.properties);
            const valueKeys = Object.keys(valueObj);
            const matchingKeys = variantKeys.filter((k) =>
              valueKeys.includes(k),
            );
            const score = matchingKeys.length;
            if (score > bestMatchScore) {
              bestMatchVariant = variant;
              bestMatchScore = score;
            }
          }

          matchingVariant =
            bestMatchVariant ||
            unionField.variants.find((v) => v.properties) ||
            null;
        }

        if (matchingVariant?.properties) {
          return [
            key,
            normalizeDefaultValues(valueObj, matchingVariant.properties),
          ];
        }

        return [key, value];
      }

      return [key, value];
    }),
  );
}

function generateFormConfig<T extends FormSchema>(schema: T) {
  const zodSchema: Record<string, FormBuilderZodField> = {};
  const defaultValues: Record<string, FormDefaultValue> = {};

  const getDefaultValueForType = (field: FormSchemaField): FormDefaultValue => {
    switch (field.type) {
      case "string":
        return field.defaultValue !== undefined ? field.defaultValue : "";
      case "number":
        return field.defaultValue;
      case "boolean":
        return field.defaultValue !== undefined ? field.defaultValue : false;
      case "date":
        return field.defaultValue;
      case "array":
        return field.defaultValue !== undefined ? field.defaultValue : [];
      case "object":
        if (field.properties) {
          const nested = generateFormConfig(field.properties);
          return nested.defaultValues;
        } else if (field.allowDynamicKeys) {
          if (field.defaultValue && typeof field.defaultValue === "object") {
            return Object.entries(field.defaultValue).map(([key, value]) => ({
              key,
              value: String(value),
            }));
          }
          return [];
        }
        return field.defaultValue !== undefined ? field.defaultValue : {};
      case "union": {
        const unionField = field as FormSchemaUnionField;

        if (unionField.defaultValue !== undefined) {
          return unionField.defaultValue;
        }

        if (unionField.nullable && !unionField.required) {
          return undefined;
        }

        const firstVariant = unionField.variants[0];
        if (!firstVariant) return undefined;

        if (!firstVariant.properties) {
          return firstVariant.value;
        }

        const variantDefaults = generateFormConfig(
          firstVariant.properties,
        ).defaultValues;

        if (unionField.discriminator) {
          return {
            [unionField.discriminator]: firstVariant.value,
            ...variantDefaults,
          };
        }

        const variantProps = firstVariant.properties || {};
        return Object.fromEntries(
          Object.entries(variantDefaults).map(([key, value]) => {
            if (value !== undefined) return [key, value];
            const fieldType = variantProps[key]?.type;
            return [key, getTypeDefault(fieldType || "string")];
          }),
        );
      }
      default:
        return undefined;
    }
  };

  Object.entries(schema).forEach(([key, field]) => {
    zodSchema[key] = createZodSchema(field);
    defaultValues[key] = getDefaultValueForType(field);
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
        (acc, [key, field]) => ({
          ...acc,
          [key]:
            field.defaultValue !== undefined
              ? field.defaultValue
              : getTypeDefault(field.type),
        }),
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
                      value={field.value ?? ""}
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
                    value={field.value ?? ""}
                    placeholder={`Enter ${fieldLabel}`}
                    disabled={disabled}
                    className="h-10"
                    onChange={(e) => field.onChange(e.target.valueAsNumber)}
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

interface DynamicObjectFieldRendererProps {
  currentPath: string;
  fieldSchema: FormSchemaObjectField;
  horizontal?: boolean;
}

const DynamicObjectFieldRenderer: React.FC<DynamicObjectFieldRendererProps> = ({
  currentPath,
  fieldSchema,
  horizontal,
}) => {
  const { control } = useFormContext();
  const { fields, append, remove, move } = useFieldArray({
    control,
    name: currentPath,
  });

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
            onClick={() => append({ key: "", value: "" })}
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
            No properties defined
          </div>
        ) : (
          <div className="space-y-2">
            {fields.map((field, index) => (
              <DynamicKeyValuePairRenderer
                key={field.id}
                fieldPath={`${currentPath}.${index}`}
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
            onClick={() => append({ key: "", value: "" })}
            disabled={fieldSchema.disabled}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Property
          </Button>
        )}

        <FormMessage />
      </div>
    </div>
  );
};

interface DynamicKeyValuePairRendererProps {
  fieldPath: string;
  index: number;
  onRemove: () => void;
  onMove: (from: number, to: number) => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  disabled?: boolean;
}

const DynamicKeyValuePairRenderer: React.FC<
  DynamicKeyValuePairRendererProps
> = ({
  fieldPath,
  index,
  onRemove,
  onMove,
  canMoveUp,
  canMoveDown,
  disabled,
}) => {
  const { control } = useFormContext();
  const [isDragging, setIsDragging] = React.useState(false);
  const [isDragOver, setIsDragOver] = React.useState(false);

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
      <div className="flex items-center gap-2 p-3">
        {(canMoveUp || canMoveDown) && (
          <div
            className="h-7 w-7 flex items-center justify-center cursor-grab active:cursor-grabbing hover:bg-accent rounded flex-shrink-0"
            title="Drag to reorder"
          >
            <GripVertical className="h-4 w-4 text-muted-foreground" />
          </div>
        )}

        <div className="flex-1 grid grid-cols-2 gap-2">
          <FormField
            control={control}
            name={`${fieldPath}.key`}
            render={({ field }) => (
              <FormItem className="space-y-0">
                <FormControl>
                  <Input
                    {...field}
                    value={field.value ?? ""}
                    placeholder="Key"
                    disabled={disabled}
                    className="h-9"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={control}
            name={`${fieldPath}.value`}
            render={({ field }) => (
              <FormItem className="space-y-0">
                <FormControl>
                  <Input
                    {...field}
                    value={field.value ?? ""}
                    placeholder="Value"
                    disabled={disabled}
                    className="h-9"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10 flex-shrink-0"
          onClick={onRemove}
          disabled={disabled}
          title="Remove property"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

interface UnionFieldRendererProps {
  currentPath: string;
  fieldSchema: FormSchemaUnionField;
  horizontal?: boolean;
}

const UnionFieldRenderer: React.FC<UnionFieldRendererProps> = ({
  currentPath,
  fieldSchema,
  horizontal,
}) => {
  const { watch, setValue } = useFormContext();
  const currentValue = watch(currentPath);

  const getActiveVariant = React.useCallback(() => {
    if (currentValue === undefined || currentValue === null) {
      if (fieldSchema.nullable) {
        return null;
      }
      return fieldSchema.variants[0] || null;
    }

    if (
      fieldSchema.discriminator &&
      typeof currentValue === "object" &&
      currentValue !== null
    ) {
      const discriminatorValue = currentValue[fieldSchema.discriminator];
      const variant = fieldSchema.variants.find(
        (v) => v.value === discriminatorValue,
      );
      if (variant) return variant;
    }

    if (typeof currentValue === "string") {
      const stringVariant = fieldSchema.variants.find((v) => !v.properties);
      if (stringVariant) return stringVariant;
    }

    if (typeof currentValue === "object" && currentValue !== null) {
      const currentKeys = Object.keys(currentValue);

      let bestMatch = fieldSchema.variants[0];
      let bestMatchScore = 0;

      for (const variant of fieldSchema.variants) {
        if (!variant.properties) continue;

        const variantKeys = Object.keys(variant.properties);
        const matchingKeys = variantKeys.filter((key) =>
          currentKeys.includes(key),
        );
        const score = matchingKeys.length;

        if (score > bestMatchScore) {
          bestMatch = variant;
          bestMatchScore = score;
        }
      }

      return bestMatch;
    }

    return fieldSchema.variants[0];
  }, [currentValue, fieldSchema]);

  const activeVariant = getActiveVariant();

  const handleVariantChange = React.useCallback(
    (variantValue: string | null) => {
      if (variantValue === null) {
        setValue(currentPath, null);
        return;
      }

      const variant = fieldSchema.variants.find(
        (v) => v.value === variantValue,
      );
      if (!variant) return;

      if (!variant.properties) {
        setValue(currentPath, variant.value);
        return;
      }

      const variantDefaults = generateFormConfig(
        variant.properties,
      ).defaultValues;

      if (fieldSchema.discriminator) {
        const normalizedDefaults = normalizeDefaultValues(
          variantDefaults,
          variant.properties,
        );
        setValue(currentPath, {
          [fieldSchema.discriminator]: variant.value,
          ...normalizedDefaults,
        });
      } else {
        const normalizedDefaults = normalizeDefaultValues(
          variantDefaults,
          variant.properties,
        );
        setValue(currentPath, normalizedDefaults);
      }
    },
    [currentPath, fieldSchema, setValue],
  );

  return (
    <div
      className={cn(
        "space-y-3",
        horizontal && "grid grid-cols-4 items-start gap-4",
      )}
    >
      <div className={cn(horizontal && "text-left pt-2")}>
        <FormLabel>
          {fieldSchema.label}
          {fieldSchema.required && (
            <span className="text-destructive ml-1">*</span>
          )}
        </FormLabel>
      </div>

      <div className={cn(horizontal && "col-span-3", "space-y-3")}>
        {fieldSchema.description && (
          <FormDescription>{fieldSchema.description}</FormDescription>
        )}

        <VariantSelector
          variants={fieldSchema.variants}
          activeVariant={activeVariant?.value || null}
          onChange={handleVariantChange}
          selectorType={fieldSchema.variantSelector || "dropdown"}
          nullable={fieldSchema.nullable}
        />

        {activeVariant && activeVariant.properties && (
          <VariantFieldsRenderer
            variantProperties={activeVariant.properties}
            currentPath={currentPath}
            collapsed={fieldSchema.collapseNested ?? true}
            horizontal={horizontal}
          />
        )}

        <FormMessage />
      </div>
    </div>
  );
};

interface VariantSelectorProps {
  variants: FormSchemaUnionVariant[];
  activeVariant: string | null;
  onChange: (value: string | null) => void;
  selectorType: "dropdown" | "tabs" | "radio";
  nullable?: boolean;
}

const VariantSelector: React.FC<VariantSelectorProps> = ({
  variants,
  activeVariant,
  onChange,
  selectorType,
  nullable,
}) => {
  const options = React.useMemo(() => {
    const opts = variants.map((v) => ({ value: v.value, label: v.label }));
    if (nullable) {
      opts.unshift({ value: "__null__", label: "None" });
    }
    return opts;
  }, [variants, nullable]);

  const handleChange = (value: string) => {
    onChange(value === "__null__" ? null : value);
  };

  switch (selectorType) {
    case "dropdown":
      return (
        <Select
          value={
            activeVariant === null ? "__null__" : activeVariant || "__null__"
          }
          onValueChange={handleChange}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select type..." />
          </SelectTrigger>
          <SelectContent>
            {options.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );

    case "tabs":
      return (
        <Tabs
          value={
            activeVariant === null ? "__null__" : activeVariant || "__null__"
          }
          onValueChange={handleChange}
        >
          <TabsList className="w-full">
            {options.map((opt) => (
              <TabsTrigger key={opt.value} value={opt.value}>
                {opt.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      );

    case "radio":
      return (
        <ToggleGroup
          type="single"
          value={
            activeVariant === null ? "__null__" : activeVariant || "__null__"
          }
          onValueChange={handleChange}
        >
          {options.map((opt) => (
            <ToggleGroupItem key={opt.value} value={opt.value}>
              {opt.label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      );

    default:
      return null;
  }
};

interface VariantFieldsRendererProps {
  variantProperties: FormSchema;
  currentPath: string;
  collapsed?: boolean;
  horizontal?: boolean;
}

const VariantFieldsRenderer: React.FC<VariantFieldsRendererProps> = ({
  variantProperties,
  currentPath,
  collapsed = true,
  horizontal,
}) => {
  const fields = Object.entries(variantProperties).filter(
    ([, field]) => !field.hidden,
  );

  if (fields.length === 0) {
    return null;
  }

  const content = (
    <div className="space-y-3 pt-2">
      {fields.map(([key, fieldSchema]) => (
        <RenderField
          key={key}
          fieldName={key}
          fieldSchema={fieldSchema}
          path={currentPath}
          horizontal={horizontal}
        />
      ))}
    </div>
  );

  if (!collapsed) {
    return content;
  }

  return (
    <Accordion type="single" collapsible defaultValue="fields">
      <AccordionItem value="fields" className="border rounded-md px-4">
        <AccordionTrigger className="hover:no-underline">
          <span className="text-sm font-medium">Configuration</span>
        </AccordionTrigger>
        <AccordionContent>{content}</AccordionContent>
      </AccordionItem>
    </Accordion>
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
                    value={field.value}
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
                      value={field.value ?? ""}
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
                    value={field.value ?? ""}
                    disabled={fieldSchema.disabled}
                    onChange={(e) => field.onChange(e.target.valueAsNumber)}
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
      if (fieldSchema.allowDynamicKeys) {
        return (
          <DynamicObjectFieldRenderer
            currentPath={currentPath}
            fieldSchema={fieldSchema}
            horizontal={horizontal}
          />
        );
      }
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

    case "union":
      return (
        <UnionFieldRenderer
          currentPath={currentPath}
          fieldSchema={fieldSchema}
          horizontal={horizontal}
        />
      );

    default:
      return null;
  }
};

interface FormBuilderProps {
  schema: FormSchema;
  defaultValues?: Record<string, FormDefaultValue>;
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
      schema,
      defaultValues: propDefaultValues,
      setForm,
      onSubmit,
      className,
      objectClassName,
      footer,
      horizontal,
    },
    _ref,
  ) {
    // Plasmic does not maintain object/array identity for props, so we
    // stringify them to use as dependencies for useMemo.
    const schemaKey = JSON.stringify(schema);
    const { zodSchema, defaultValues: schemaDefaultValues } =
      React.useMemo(() => {
        if (!schema || Object.keys(schema).length === 0) {
          return {
            zodSchema: z.object({}),
            defaultValues: {},
          };
        }
        return generateFormConfig(schema);
      }, [schemaKey]);

    const mergedDefaultValues = React.useMemo(
      () => {
        if (!propDefaultValues || Object.keys(propDefaultValues).length === 0) {
          return schemaDefaultValues;
        }
        const normalizedPropDefaults = normalizeDefaultValues(
          propDefaultValues,
          schema,
        );
        return { ...schemaDefaultValues, ...normalizedPropDefaults };
      },
      [], // The default values are only computed once on mount
    );

    const form = useForm<z.infer<typeof zodSchema>>({
      resolver: zodResolver(zodSchema),
      defaultValues: mergedDefaultValues,
    });

    React.useEffect(() => {
      setForm?.(form);
    }, [form]);

    React.useEffect(() => {
      if (schema && Object.keys(schema).length > 0) {
        form.reset(mergedDefaultValues);
      }
    }, [schemaKey]);

    return (
      <FormProvider {...form}>
        <Form {...form}>
          <form
            onSubmit={safeSubmit(
              form.handleSubmit((x) => onSubmit(stripUndefinedDeep(x))),
            )}
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

            <FormErrorBanner schema={schema} />

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
    defaultValues: {
      type: "object",
      description:
        "Default values for form fields. Maps 1:1 with schema keys and overrides schema defaultValue fields.",
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
