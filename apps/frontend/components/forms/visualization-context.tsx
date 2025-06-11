import _ from "lodash";
import dayjs from "dayjs";
import { Formik, FormikProps } from "formik";
import React, { ReactNode } from "react";
import qs from "qs";
import * as Yup from "yup";
import { DataProvider } from "@plasmicapp/loader-nextjs";
import { FormContext } from "@/components/forms/form-elements";

const DEFAULT_START_TIME = dayjs().subtract(1, "year");
const DEFAULT_END_TIME = dayjs();
const DEFAULT_FORM_DATA: VisualizationContextData = {
  startDate: DEFAULT_START_TIME.format("YYYY-MM-DD"),
  endDate: DEFAULT_END_TIME.format("YYYY-MM-DD"),
};

interface VisualizationContextData {
  startDate: string;
  endDate: string;
}

/**
 * Converts a query string into raw form data
 * @param query
 * @returns
 */
const queryStringToFormData = (query?: string) => {
  const rawValues = qs.parse(query ?? "");
  const values = {
    ...rawValues,
  };
  return values as any;
};

/**
 * Converts raw form data to a query string
 * @param values
 * @returns
 */
const formDataToQueryString = (values: Record<string, any>) => {
  // We will serialize our Dayjs objects
  ["startDate", "endDate"].forEach((key: string) => {
    if (values[key] && values[key].format) {
      values[key] = values[key].format("YYYY-MM-DD");
    }
  });
  const filteredValues = _.chain(values).pickBy().value();
  return qs.stringify(filteredValues);
};

/**
 * Form validation rules
 */
const ValidationSchema = Yup.object().shape({
  startDate: Yup.date(),
  endDate: Yup.date().when("startDate", (startDate) => {
    return Yup.date().min(startDate, "End date must be after start date");
  }),
});

/**
 * Visualization Context
 * - For the actual layout of form elements,
 *   we assume it's passed in via the `children` prop.
 * - Use the form elements defined in `./form-elements.tsx`
 * - Make sure that there is a form element with a `fieldName`
 *   for each field in VisualizationContextData
 */
export interface VisualizationContextProps {
  className?: string; // Plasmic CSS class
  variableName: string; // Name to use in Plasmic data picker
  children: ReactNode; // Form elements
}

export function VisualizationContext(props: VisualizationContextProps) {
  const { className, variableName, children } = props;

  // Query string
  const [initialQuery, setInitialQuery] = React.useState<string | undefined>(
    undefined,
  );
  // Load the querystring into React state only once on initial page load
  React.useEffect(() => {
    if (!initialQuery) {
      window.location.hash.startsWith("#")
        ? setInitialQuery(window.location.hash.slice(1))
        : setInitialQuery(window.location.hash);
    }
  }, [initialQuery]);

  const onComplete = async (values: VisualizationContextData) => {
    console.log("Submit: ", values);
  };

  return (
    <div className={className}>
      <Formik
        validationSchema={ValidationSchema}
        validateOnMount={true}
        validate={(_values) => {
          // console.log(values);
          if (typeof initialQuery !== "undefined") {
            // The useEffect has run already, so it's safe to just update the query string directly
            //const querystring = formDataToQueryString(values);
            //const path = `${window.location.pathname}#${querystring}`;
            //window.history.pushState(null, "", path);
          }
        }}
        initialValues={{
          ...DEFAULT_FORM_DATA,
          ...queryStringToFormData(initialQuery),
        }}
        enableReinitialize
        onSubmit={async (values, { setSubmitting }) => {
          await onComplete(values);
          setSubmitting(false);
        }}
      >
        {(formikProps: FormikProps<VisualizationContextData>) => (
          <DataProvider
            name={variableName}
            data={{
              ...formikProps.values,
              shareUrl: `${window.location.pathname}#${formDataToQueryString(
                formikProps.values,
              )}`,
              isSubmitting: formikProps.isSubmitting,
            }}
          >
            <FormContext.Provider value={formikProps}>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  console.log("Submitting form...");
                  console.log("Form values: ", formikProps.values);
                  console.log("Form errors: ", formikProps.errors);
                  formikProps.handleSubmit();
                }}
              >
                {children}
              </form>
            </FormContext.Provider>
          </DataProvider>
        )}
      </Formik>
    </div>
  );
}
