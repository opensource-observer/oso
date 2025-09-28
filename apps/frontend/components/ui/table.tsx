import * as React from "react";
import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import { cn } from "@/lib/utils";

type TableProps = React.HTMLAttributes<HTMLTableElement>;

const Table = React.forwardRef<HTMLTableElement, TableProps>(
  ({ className, ...props }, ref) => (
    <div className="relative w-full overflow-auto">
      <table
        ref={ref}
        className={cn("w-full caption-bottom text-sm", className)}
        {...props}
      />
    </div>
  ),
);
Table.displayName = "Table";

const TableMeta: CodeComponentMeta<TableProps> = {
  name: "Table",
  description: "shadcn/ui Table component",
  props: {
    children: "slot",
  },
};

type TableHeaderProps = React.HTMLAttributes<HTMLTableSectionElement>;

const TableHeader = React.forwardRef<HTMLTableSectionElement, TableHeaderProps>(
  ({ className, ...props }, ref) => (
    <thead ref={ref} className={cn("[&_tr]:border-b", className)} {...props} />
  ),
);
TableHeader.displayName = "TableHeader";

const TableHeaderMeta: CodeComponentMeta<TableHeaderProps> = {
  name: "TableHeader",
  description: "shadcn/ui TableHeader component",
  props: {
    children: "slot",
  },
};

type TableBodyProps = React.HTMLAttributes<HTMLTableSectionElement>;

const TableBody = React.forwardRef<HTMLTableSectionElement, TableBodyProps>(
  ({ className, ...props }, ref) => (
    <tbody
      ref={ref}
      className={cn("[&_tr:last-child]:border-0", className)}
      {...props}
    />
  ),
);
TableBody.displayName = "TableBody";

const TableBodyMeta: CodeComponentMeta<TableBodyProps> = {
  name: "TableBody",
  description: "shadcn/ui TableBody component",
  props: {
    children: "slot",
  },
};

type TableFooterProps = React.HTMLAttributes<HTMLTableSectionElement>;

const TableFooter = React.forwardRef<HTMLTableSectionElement, TableFooterProps>(
  ({ className, ...props }, ref) => (
    <tfoot
      ref={ref}
      className={cn(
        "border-t bg-muted/50 font-medium [&>tr]:last:border-b-0",
        className,
      )}
      {...props}
    />
  ),
);
TableFooter.displayName = "TableFooter";

const TableFooterMeta: CodeComponentMeta<TableFooterProps> = {
  name: "TableFooter",
  description: "shadcn/ui TableFooter component",
  props: {
    children: "slot",
  },
};

type TableRowProps = React.HTMLAttributes<HTMLTableRowElement>;

const TableRow = React.forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ className, ...props }, ref) => (
    <tr
      ref={ref}
      className={cn(
        "border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted",
        className,
      )}
      {...props}
    />
  ),
);
TableRow.displayName = "TableRow";

const TableRowMeta: CodeComponentMeta<TableRowProps> = {
  name: "TableRow",
  description: "shadcn/ui TableRow component",
  props: {
    children: "slot",
  },
};

type TableHeadProps = React.ThHTMLAttributes<HTMLTableCellElement>;

const TableHead = React.forwardRef<HTMLTableCellElement, TableHeadProps>(
  ({ className, ...props }, ref) => (
    <th
      ref={ref}
      className={cn(
        "h-10 px-2 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
        className,
      )}
      {...props}
    />
  ),
);
TableHead.displayName = "TableHead";

const TableHeadMeta: CodeComponentMeta<TableHeadProps> = {
  name: "TableHead",
  description: "shadcn/ui TableHead component",
  props: {
    children: "slot",
  },
};

type TableCellProps = React.TdHTMLAttributes<HTMLTableCellElement>;

const TableCell = React.forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ className, ...props }, ref) => (
    <td
      ref={ref}
      className={cn(
        "p-2 align-middle [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
        className,
      )}
      {...props}
    />
  ),
);
TableCell.displayName = "TableCell";

const TableCellMeta: CodeComponentMeta<TableCellProps> = {
  name: "TableCell",
  description: "shadcn/ui TableCell component",
  props: {
    children: "slot",
  },
};

type TableCaptionProps = React.HTMLAttributes<HTMLTableCaptionElement>;

const TableCaption = React.forwardRef<
  HTMLTableCaptionElement,
  TableCaptionProps
>(({ className, ...props }, ref) => (
  <caption
    ref={ref}
    className={cn("mt-4 text-sm text-muted-foreground", className)}
    {...props}
  />
));
TableCaption.displayName = "TableCaption";

const TableCaptionMeta: CodeComponentMeta<TableCaptionProps> = {
  name: "TableCaption",
  description: "shadcn/ui TableCaption component",
  props: {
    children: "slot",
  },
};

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
  // Meta
  TableMeta,
  TableHeaderMeta,
  TableBodyMeta,
  TableFooterMeta,
  TableHeadMeta,
  TableRowMeta,
  TableCellMeta,
  TableCaptionMeta,
};
