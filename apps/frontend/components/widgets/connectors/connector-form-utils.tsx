import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { DYNAMIC_CONNECTOR_NAME_REGEX } from "@/lib/types/dynamic-connector";
import { Control, FieldPath } from "react-hook-form";
import { z } from "zod";

const connectorNameSchema = z
  .string()
  .min(1, "Connector name is required")
  .refine(
    (val) => DYNAMIC_CONNECTOR_NAME_REGEX.test(val),
    "Invalid name, valid characters are a-z 0-9 _ -",
  );

function ConnectorNameField<T extends { connector_name: string }>({
  control,
}: {
  control: Control<T>;
}) {
  return (
    <FormField
      control={control}
      name={"connector_name" as FieldPath<T>}
      render={({ field }) => (
        <FormItem>
          <FormLabel>Connector Name</FormLabel>
          <FormControl>
            <Input {...field} />
          </FormControl>
          <FormMessage>
            <span className="text-sm text-muted-foreground">
              Valid characters are a-z 0-9 _
              <br />
              The organization name will be automatically added as a prefix.
            </span>
          </FormMessage>
        </FormItem>
      )}
    />
  );
}

export { connectorNameSchema, ConnectorNameField };
