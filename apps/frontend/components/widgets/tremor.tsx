import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import {
  BarList as BarListTremor,
  BarListProps,
  AreaChartProps,
} from "@tremor/react";

const AreaChartMeta: CodeComponentMeta<AreaChartProps> = {
  name: "AreaChart",
  description: "Tremor AreaChart",
  props: {
    data: {
      type: "array",
      defaultValue: [],
    },
    categories: {
      type: "array",
    },
    index: {
      type: "string",
      helpText: "Name of the index column",
      defaultValue: "date",
    },
    colors: {
      type: "array",
    },
    startEndOnly: "boolean",
    showXAxis: "boolean",
    showYAxis: "boolean",
    yAxisWidth: "number",
    showAnimation: "boolean",
    animationDuration: "number",
    showTooltip: "boolean",
    showLegend: "boolean",
    showGridLines: "boolean",
    showGradient: "boolean",
    autoMinValue: "boolean",
    minValue: "number",
    maxValue: "number",
    stack: "boolean",
    curveType: {
      type: "choice",
      options: ["linear", "step", "monotone"],
    },
    connectNulls: "boolean",
    allowDecimals: "boolean",
    noDataText: "string",
  },
};

const BarListMeta: CodeComponentMeta<BarListProps> = {
  name: "BarList",
  description: "Tremor BarList",
  props: {
    data: {
      type: "array",
      defaultValue: [],
    },
    colors: {
      type: "array",
      defaultValue: ["blue"],
    },
    showAnimation: "boolean",
  },
};

function BarList(props: BarListProps) {
  return (
    <BarListTremor
      {...props}
      valueFormatter={(value: number) => value.toLocaleString()}
    />
  );
}

export { AreaChartMeta, BarList, BarListMeta };
