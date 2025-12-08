import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { Upload } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

type FileInputProps = React.ComponentProps<"input">;

const FileInput = React.forwardRef<HTMLInputElement, FileInputProps>(
  ({ className, onChange, ...props }, ref) => {
    const [isDragActive, setIsDragActive] = React.useState(false);
    const [fileName, setFileName] = React.useState<string | null>(null);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        setFileName(
          e.target.files.length > 1
            ? `${e.target.files.length} files selected`
            : e.target.files[0].name,
        );
      } else {
        setFileName(null);
      }
      onChange?.(e);
    };

    return (
      <div
        className={cn(
          "relative flex flex-col items-center justify-center w-full h-32 rounded-md border-2 border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors",
          isDragActive ? "border-primary bg-primary/5" : "hover:bg-muted/5",
          props.disabled &&
            "opacity-50 cursor-not-allowed hover:bg-transparent",
          className,
        )}
        onDragOver={(e) => {
          e.preventDefault();
          if (!props.disabled) setIsDragActive(true);
        }}
        onDragLeave={() => setIsDragActive(false)}
        onDrop={() => setIsDragActive(false)}
      >
        <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground pointer-events-none">
          <Upload className="h-8 w-8" />
          {fileName ? (
            <p className="font-medium text-foreground">{fileName}</p>
          ) : (
            <p>Drag & drop or click to upload</p>
          )}
        </div>
        <input
          type="file"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          ref={ref}
          onChange={handleChange}
          {...props}
        />
      </div>
    );
  },
);
FileInput.displayName = "FileInput";

const FileInputMeta: CodeComponentMeta<FileInputProps> = {
  name: "FileInput",
  description: "shadcn/ui File input component",
  props: {
    onChange: {
      type: "eventHandler",
      argTypes: [{ name: "event", type: "object" }],
    },
    disabled: "boolean",
    multiple: "boolean",
    accept: "string",
  },
  states: {
    files: {
      type: "readonly",
      variableType: "object",
      onChangeProp: "onChange",
      onChangeArgsToValue: (event) => event.target.files,
    },
  },
};

export { FileInput, FileInputMeta };
