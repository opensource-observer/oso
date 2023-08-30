import React from "react";
import { Field, FieldProps, ErrorMessage, FormikProps } from "formik";

/**
 * Constants
 */
const MISSING_FIELDNAME_ERROR = "Missing required `fieldName` prop";

/**
 * Context used to store props from Formik
 * - Only used as a workaround when we don't have other ways
 *   to Formik state (e.g. when using DatePicker from formik-mui)
 */
export const FormContext = React.createContext<FormikProps<any> | undefined>(
  undefined,
);

/**
 * Used to wrap any Form input for Formik
 * This has been tested on unstyled text inputs,
 * but unclear if it'd work with anything else (e.g. Select)
 */
export interface FormFieldProps {
  className?: string; // Plasmic CSS class
  fieldName?: string; // Formik field name
  children?: any; // Form element
}

export function FormField(props: FormFieldProps) {
  const { className, fieldName, children } = props;

  // Developer error messages surfaced to the UI
  if (!fieldName) {
    return <div>{MISSING_FIELDNAME_ERROR}</div>;
  } else if (!children) {
    return <div>Add an input into the `children` slot</div>;
  }

  return (
    <Field name={fieldName}>
      {(fieldProps: FieldProps) =>
        React.cloneElement(children, {
          ...children.props,
          ...fieldProps.field,
          className,
        })
      }
    </Field>
  );
}

/**
 * Displays an error message from Formik
 */
export interface FormErrorProps {
  className?: string; // Plasmic CSS class
  fieldName?: string; // Formik field name
}

export function FormError(props: FormErrorProps) {
  const { className, fieldName } = props;

  // Developer error messages surfaced to the UI
  if (!fieldName) {
    return <div>{MISSING_FIELDNAME_ERROR}</div>;
  }
  return (
    <div className={className}>
      <ErrorMessage name={fieldName} />
    </div>
  );
}
