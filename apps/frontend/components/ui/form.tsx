"use client";

import * as React from "react";
import * as LabelPrimitive from "@radix-ui/react-label";
import { Slot } from "@radix-ui/react-slot";
import {
  Controller,
  FormProvider,
  useFormContext,
  type ControllerProps,
  type FieldPath,
  type FieldValues,
} from "react-hook-form";

import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";

import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";

const Form = FormProvider;

type FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> = {
  name: TName;
};

const FormFieldContext = React.createContext<FormFieldContextValue>(
  {} as FormFieldContextValue,
);

const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  ...props
}: ControllerProps<TFieldValues, TName>) => {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  );
};

const useFormField = () => {
  const fieldContext = React.useContext(FormFieldContext);
  const itemContext = React.useContext(FormItemContext);
  const { getFieldState, formState } = useFormContext();

  const fieldState = getFieldState(fieldContext.name, formState);

  if (!fieldContext) {
    throw new Error("useFormField should be used within <FormField>");
  }

  const { id } = itemContext;

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  };
};

type FormItemContextValue = {
  id: string;
};

const FormItemContext = React.createContext<FormItemContextValue>(
  {} as FormItemContextValue,
);

type FormItemProps = React.HTMLAttributes<HTMLDivElement>;

const FormItem = React.forwardRef<HTMLDivElement, FormItemProps>(
  ({ className, ...props }, ref) => {
    const id = React.useId();

    return (
      <FormItemContext.Provider value={{ id }}>
        <div ref={ref} className={cn("space-y-2", className)} {...props} />
      </FormItemContext.Provider>
    );
  },
);
FormItem.displayName = "FormItem";

const FormItemMeta: CodeComponentMeta<FormItemProps> = {
  name: "FormItem",
  description: "shadcn/ui FormItem component",
  props: {
    children: "slot",
  },
};

type FormLabelProps = React.ComponentPropsWithoutRef<
  typeof LabelPrimitive.Root
>;

const FormLabel = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  FormLabelProps
>(({ className, ...props }, ref) => {
  const { error, formItemId } = useFormField();

  return (
    <Label
      ref={ref}
      className={cn(error && "text-destructive", className)}
      htmlFor={formItemId}
      {...props}
    />
  );
});
FormLabel.displayName = "FormLabel";

const FormLabelMeta: CodeComponentMeta<FormLabelProps> = {
  name: "FormLabel",
  description: "shadcn/ui FormLabel component",
  props: {
    children: "slot",
  },
};

type FormControlProps = React.ComponentPropsWithoutRef<typeof Slot>;

const FormControl = React.forwardRef<
  React.ElementRef<typeof Slot>,
  FormControlProps
>(({ ...props }, ref) => {
  const { error, formItemId, formDescriptionId, formMessageId } =
    useFormField();

  return (
    <Slot
      ref={ref}
      id={formItemId}
      aria-describedby={
        !error
          ? `${formDescriptionId}`
          : `${formDescriptionId} ${formMessageId}`
      }
      aria-invalid={!!error}
      {...props}
    />
  );
});
FormControl.displayName = "FormControl";

const FormControlMeta: CodeComponentMeta<FormControlProps> = {
  name: "FormControl",
  description: "shadcn/ui FormControl component",
  props: {
    children: "slot",
  },
};

type FormDescriptionProps = React.HTMLAttributes<HTMLParagraphElement>;

const FormDescription = React.forwardRef<
  HTMLParagraphElement,
  FormDescriptionProps
>(({ className, ...props }, ref) => {
  const { formDescriptionId } = useFormField();

  return (
    <p
      ref={ref}
      id={formDescriptionId}
      className={cn("text-[0.8rem] text-muted-foreground", className)}
      {...props}
    />
  );
});
FormDescription.displayName = "FormDescription";

const FormDescriptionMeta: CodeComponentMeta<FormDescriptionProps> = {
  name: "FormDescription",
  description: "shadcn/ui FormDescription component",
  props: {
    children: "slot",
  },
};

type FormMessageProps = React.HTMLAttributes<HTMLParagraphElement>;

const FormMessage = React.forwardRef<HTMLParagraphElement, FormMessageProps>(
  ({ className, children, ...props }, ref) => {
    const { error, formMessageId } = useFormField();
    const body = error ? String(error?.message ?? "") : children;

    if (!body) {
      return null;
    }

    return (
      <p
        ref={ref}
        id={formMessageId}
        className={cn("text-[0.8rem] font-medium text-destructive", className)}
        {...props}
      >
        {body}
      </p>
    );
  },
);
FormMessage.displayName = "FormMessage";

const FormMessageMeta: CodeComponentMeta<FormMessageProps> = {
  name: "FormMessage",
  description: "shadcn/ui FormMessage component",
  props: {
    children: "slot",
  },
};

// Needed because of https://github.com/orgs/react-hook-form/discussions/8020
function safeSubmit<T>(promise: (event: React.SyntheticEvent) => Promise<T>) {
  return (event: React.SyntheticEvent) => {
    if (promise) {
      promise(event).catch((error) => {
        console.log("Unexpected error", error);
      });
    }
  };
}

export {
  useFormField,
  Form,
  FormItem,
  FormItemMeta,
  FormLabel,
  FormLabelMeta,
  FormControl,
  FormControlMeta,
  FormDescription,
  FormDescriptionMeta,
  FormMessage,
  FormMessageMeta,
  FormField,
  safeSubmit,
};
