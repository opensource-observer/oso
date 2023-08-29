import _ from "lodash";
import React from "react";
import Checkbox from "@mui/material/Checkbox";
import FormControl from "@mui/material/FormControl";
import FormHelperText from "@mui/material/FormHelperText";
import InputLabel from "@mui/material/InputLabel";
import ListItemText from "@mui/material/ListItemText";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Slider from "@mui/material/Slider";
import TextField from "@mui/material/TextField";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { Field, FieldProps, ErrorMessage, FormikProps } from "formik";
import { DatePicker } from "formik-mui-x-date-pickers";
//import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import Dropzone from "react-dropzone";

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

/**
 * Formik-wrapped TextField
 */
export interface FormTextFieldProps {
  className?: string; // Plasmic CSS class
  fieldName?: string; // Formik field name
  disabled?: boolean; // Disabled
  label?: string; // Label to show
  placeholder?: string; // Input placeholder
  multiline?: boolean; // Enable multiline, autosized by default
  minRows?: number; // If multiline is true, bound it
  maxRows?: number; // If multiline is true, bound it
  rows?: number; // Fixed number of rows to show in multi-line inputs
}

export function FormTextField(props: FormTextFieldProps) {
  const {
    className,
    fieldName,
    disabled,
    label,
    placeholder,
    multiline,
    minRows,
    maxRows,
    rows,
  } = props;

  // Developer error messages surfaced to the UI
  if (!fieldName) {
    return <div>{MISSING_FIELDNAME_ERROR}</div>;
  }

  return (
    <Field name={fieldName}>
      {({ field, meta }: FieldProps) => (
        <TextField
          {...field}
          className={className}
          variant={"outlined"}
          disabled={disabled}
          label={label}
          placeholder={placeholder}
          multiline={multiline}
          minRows={minRows}
          maxRows={maxRows}
          rows={rows}
          error={meta.touched && !!meta.error}
          helperText={meta.touched ? meta.error : undefined}
        />
      )}
    </Field>
  );
}

/**
 * Formik-wrapped Select
 * - Currently we use the same string as the label and value of a Select Option
 *   Future work to allow different values
 */
export interface FormSelectProps {
  className?: string; // Plasmic CSS class
  fieldName?: string; // Formik field name
  label?: string; // Label to show
  optionValues?: any; // e.g. ["val1", "val2"]
  multiple?: boolean; // Allow multi-select
  disabled?: boolean; // Disable select
}

export function FormSelect(props: FormSelectProps) {
  const { className, fieldName, label, optionValues, multiple, disabled } =
    props;

  // Developer error messages surfaced to the UI
  if (!fieldName) {
    return <div>{MISSING_FIELDNAME_ERROR}</div>;
  } else if (!_.isArray(optionValues)) {
    return <div>`optionValues` must be an array of strings</div>;
  }

  return (
    <Field name={fieldName}>
      {({ field, meta }: FieldProps) => (
        <FormControl
          sx={{ m: 1, minWidth: 120 }}
          className={className}
          error={meta.touched && !!meta.error}
          disabled={disabled}
        >
          <InputLabel>{label}</InputLabel>
          <Select
            {...field}
            variant={"outlined"}
            label={label}
            multiple={multiple}
            renderValue={(selected: string[] | string) =>
              _.isArray(selected) ? selected.join(", ") : selected
            }
          >
            {optionValues.map((val) => (
              <MenuItem key={val} value={val}>
                {multiple && (
                  <Checkbox
                    checked={
                      _.isArray(field.value)
                        ? field.value.includes(val)
                        : field.value === val
                    }
                  />
                )}
                <ListItemText primary={val} />
              </MenuItem>
            ))}
          </Select>
          <FormHelperText>
            {meta.touched ? meta.error : undefined}
          </FormHelperText>
        </FormControl>
      )}
    </Field>
  );
}

/**
 * Formik-wrapped Slider
 */
export interface FormSliderProps {
  className?: string; // Plasmic CSS class
  fieldName?: string; // Formik field name
  disabled?: boolean; // Disabled
  defaultValue?: number; // Default value
  min?: number; // Minimum value
  max?: number; // Maximum value
  step?: number; // Granularity of slider
}

export function FormSlider(props: FormSliderProps) {
  const { className, fieldName, disabled, defaultValue, min, max, step } =
    props;

  // Developer error messages surfaced to the UI
  if (!fieldName) {
    return <div>{MISSING_FIELDNAME_ERROR}</div>;
  }

  return (
    <Field name={fieldName}>
      {({ field }: FieldProps) => (
        <Slider
          {...field}
          className={className}
          valueLabelDisplay="auto"
          disabled={disabled}
          defaultValue={defaultValue}
          min={min}
          max={max}
          step={step}
        />
      )}
    </Field>
  );
}

/**
 * Formik-wrapped DatePicker
 */
export interface FormDatePickerProps {
  className?: string; // Plasmic CSS class
  fieldName?: string; // Formik field name
  label?: string; // Label to show
  disabled?: boolean; // disable this
}

export function FormDatePicker(props: FormDatePickerProps) {
  const { className, fieldName, label, disabled } = props;
  const formikProps = React.useContext(FormContext);

  // Developer error messages surfaced to the UI
  if (!fieldName) {
    return <div>{MISSING_FIELDNAME_ERROR}</div>;
  }

  // Retrieve the FormikProps in a workaround context to get the errors
  const hasError =
    formikProps &&
    formikProps.touched[fieldName] &&
    !!formikProps.errors[fieldName];
  const errorMessage = hasError
    ? (formikProps.errors[fieldName] as string)
    : undefined;

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Field
        className={className}
        component={DatePicker}
        name={fieldName}
        label={label}
        disabled={disabled}
        textField={{
          variant: "outlined",
          error: hasError,
          helperText: errorMessage,
          disabled,
        }}
      />
    </LocalizationProvider>
  );

  /**
  // This be the way we implement this in theory, but for some reason
  // the MUI DatePicker onChange function is missing event.target
  // which breaks Formik when it processes the event.
  // We use formik-mui as a workaround for now.
  return (
    <Field name={fieldName}>
      {({
        field,
        form,
        meta,
      }: FieldProps) => (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <DatePicker
            {...field}
            className={className}
            label={label}
            renderInput={(params) => (
              <TextField
                {...params}
                error={meta.touched && !!meta.error}
                helperText={meta.touched ? meta.error : undefined}
              />
            )}
          />
        </LocalizationProvider>
      )}
    </Field>
  );
 */
}

/**
 * Formik-wrapped Dropzone
 * - Uses 'react-mui-dropzone' until MUI supports this natively
 *  See https://mui.com/material-ui/discover-more/roadmap/#new-components
 */
export interface FormDropZoneProps {
  className?: string; // Plasmic CSS class
  fieldName?: string; // Formik field name
  accept: string;
  children?: any; // Form element
}

export function FormDropZone(props: FormDropZoneProps) {
  const { className, fieldName, children, accept } = props;
  const formikProps = React.useContext(FormContext);

  // Developer error messages surfaced to the UI
  if (!fieldName) {
    return <div>{MISSING_FIELDNAME_ERROR}</div>;
  } else if (!children) {
    return <div>Add an input into the `children` slot</div>;
  }

  return (
    <Field name={fieldName}>
      {() => (
        <Dropzone
          onDrop={(acceptedFiles: any) => {
            formikProps?.setFieldValue(fieldName, acceptedFiles[0]);
          }}
          accept={accept ? { [accept]: [] } : {}}
        >
          {({ getRootProps, getInputProps }) => (
            <div {...getRootProps()} className={className}>
              <input {...getInputProps()} accept={accept} />
              {children}
            </div>
          )}
        </Dropzone>
      )}
    </Field>
  );
}

/**
 * Formik-wrapped Checkbox
 * - Just the checkbox. For labels, group in Plasmic
 */
export interface FormCheckboxProps {
  className?: string; // Plasmic CSS class
  fieldName?: string; // Formik field name
}

export function FormCheckbox(props: FormCheckboxProps) {
  const { className, fieldName } = props;

  if (!fieldName) {
    return <div>{MISSING_FIELDNAME_ERROR}</div>;
  }

  return <Field type="checkbox" className={className} name={fieldName} />;
  /**
   * // Would have been nice to use MUI, but for some reason the visual check box is unable to stay in sync with the form data. (e.g. with initial values)
  return (
    <Field name={fieldName} className={className}>
      {({ field }: FieldProps) => (
        <Checkbox
          {...field}
          defaultChecked={defaultChecked}
          disabled={disabled}
        />
      )}
    </Field>
  );
  */
}
