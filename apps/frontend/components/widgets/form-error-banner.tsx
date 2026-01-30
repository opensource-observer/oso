"use client";

import * as React from "react";
import { useFormContext, FieldErrors } from "react-hook-form";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { AlertCircle, XCircle } from "lucide-react";

interface FormSchemaFieldBase {
  label: string;
  required?: boolean;
  description?: string;
  defaultValue?: unknown;
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

interface ErrorItem {
  id: string;
  path: string;
  label: string;
  message: string;
}

interface FormErrorBannerProps {
  schema: FormSchema;
}

function getFieldLabel(path: string, schema: FormSchema): string {
  const parts = path.split(".");
  let currentSchema: FormSchema | undefined = schema;
  const labels: string[] = [];

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];

    if (!currentSchema) {
      break;
    }

    if (/^\d+$/.test(part)) {
      const index = parseInt(part, 10);
      labels.push(`Item ${index + 1}`);
      continue;
    }

    const field: FormSchemaField | undefined = currentSchema[part];
    if (!field) {
      labels.push(part);
      continue;
    }

    let label = field.label;
    if (field.advanced && field.advancedGroup) {
      label = `(${field.advancedGroup}) ${label}`;
    }
    labels.push(label);

    if (field.type === "object" && field.properties) {
      currentSchema = field.properties;
    } else if (field.type === "array" && field.itemProperties) {
      currentSchema = field.itemProperties;
    } else if (field.type === "union") {
      currentSchema = undefined;
    } else {
      currentSchema = undefined;
    }
  }

  return labels.join(" > ");
}

function parseFormErrors(
  errors: FieldErrors,
  schema: FormSchema,
  pathPrefix = "",
): ErrorItem[] {
  const errorItems: ErrorItem[] = [];

  for (const [key, error] of Object.entries(errors)) {
    const currentPath = pathPrefix ? `${pathPrefix}.${key}` : key;

    if (!error) continue;

    if (error.message && typeof error.message === "string") {
      errorItems.push({
        id: currentPath,
        path: currentPath,
        label: getFieldLabel(currentPath, schema),
        message: error.message,
      });
    }

    if (typeof error === "object" && !error.message) {
      const nestedErrors = parseFormErrors(
        error as FieldErrors,
        schema,
        currentPath,
      );
      errorItems.push(...nestedErrors);
    }
  }

  return errorItems;
}

function scrollToField(fieldPath: string) {
  const field = document.querySelector(
    `[name="${fieldPath}"]`,
  ) as HTMLElement | null;

  if (!field) {
    console.warn(`Could not find field with path: ${fieldPath}`);
    return;
  }

  const advancedAccordion = field.closest('[data-state="closed"]');
  if (advancedAccordion) {
    const trigger = advancedAccordion.querySelector(
      "[data-radix-collection-item]",
    ) as HTMLElement | null;
    if (trigger) {
      trigger.click();
      setTimeout(() => {
        field.scrollIntoView({ behavior: "smooth", block: "center" });
        field.focus();
      }, 100);
      return;
    }
  }

  field.scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => field.focus(), 100);
}

export const FormErrorBanner: React.FC<FormErrorBannerProps> = ({ schema }) => {
  const { formState } = useFormContext();
  const { errors } = formState;

  const errorItems = React.useMemo(
    () => parseFormErrors(errors, schema),
    [errors, schema],
  );

  if (errorItems.length === 0) return null;

  return (
    <Alert variant="destructive" className="mt-6">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>
        {errorItems.length} field{errorItems.length > 1 ? "s" : ""} need
        attention
      </AlertTitle>
      <AlertDescription>
        <Accordion
          type="multiple"
          defaultValue={errorItems.map((item) => item.id)}
          className="w-full"
        >
          {errorItems.map((item) => (
            <AccordionItem key={item.id} value={item.id}>
              <AccordionTrigger
                onClick={(e) => {
                  e.preventDefault();
                  scrollToField(item.path);
                }}
                className="hover:no-underline"
              >
                <div className="flex items-center gap-2">
                  <XCircle className="h-3.5 w-3.5" />
                  <span className="font-medium text-left">{item.label}</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <p className="text-sm">{item.message}</p>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </AlertDescription>
    </Alert>
  );
};
