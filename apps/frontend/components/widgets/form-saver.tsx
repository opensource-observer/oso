import { CodeComponentMeta, DataProvider } from "@plasmicapp/loader-nextjs";
import { debounce } from "lodash";
import React from "react";
import { UseFormReturn } from "react-hook-form";

interface FormSaverProps {
  form?: UseFormReturn<any>;
  onSave?: (values: any) => Promise<void>;
}

function FormSaver({
  form,
  onSave,
  children,
}: React.PropsWithChildren<FormSaverProps>) {
  const [isDirtyState, setIsDirtyState] = React.useState<any>(false);
  const debounceSave = React.useCallback(
    debounce(
      ({ values, isDirty }: { values: any; isDirty: boolean | undefined }) => {
        if (!isDirty) {
          console.log("Form not dirty, skipping Form save.");
          return;
        }
        console.log("Auto-saving form Form with values:", values);
        onSave?.(values)
          .then(() => console.log("Auto-save successful."))
          .catch((err) => {
            console.log("Error during auto-save:", err);
          });
      },
      3000,
      { maxWait: 10000 },
    ),
    [form, onSave],
  );

  React.useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s" && form) {
        e.preventDefault();
        console.log("Manual save triggered via keyboard shortcut.");
        void onSave?.(form.getValues());
      }
    };
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirtyState) {
        e.preventDefault();
        return "Unsaved changes";
      }
    };
    window.addEventListener("keydown", handleKeyPress);

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      if (isDirtyState && form) {
        console.log(
          "Component unmounting with dirty form, attempting to save.",
        );
        void onSave?.(form.getValues());
      }
      window.removeEventListener("keydown", handleKeyPress);
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [isDirtyState, form, onSave]);

  React.useEffect(() => {
    if (!form) {
      return;
    }

    const unsubscribe = form.subscribe({
      formState: {
        values: true,
      },
      callback: ({ values, isDirty }) => {
        setIsDirtyState(isDirty);
        console.log("Form changed, scheduling auto-save. isDirty:", isDirty);
        debounceSave({ values, isDirty });
      },
    });
    return () => unsubscribe();
  }, [form]);

  return (
    <DataProvider name="isFormDirty" data={isDirtyState}>
      {children}
    </DataProvider>
  );
}

const FormSaverMeta: CodeComponentMeta<FormSaverProps> = {
  name: "FormSaver",
  props: {
    form: "object",
    onSave: {
      type: "eventHandler",
      argTypes: [
        {
          name: "data",
          type: "object",
        },
      ],
    },
    children: "slot",
  },
  providesData: true,
};

export { FormSaver, FormSaverMeta };
