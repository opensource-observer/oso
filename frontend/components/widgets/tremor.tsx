import { BarList as BarListTremor, BarListProps } from "@tremor/react";

function BarList(props: BarListProps) {
  return (
    <BarListTremor
      {...props}
      valueFormatter={(value: number) => value.toLocaleString()}
    />
  );
}

export { BarList };
