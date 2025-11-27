"use client";

import { CodeComponentMeta } from "@plasmicapp/loader-nextjs";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  RowSelectionState,
  useReactTable,
  Table as TableState,
  Row,
  Column,
  RowData,
} from "@tanstack/react-table";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  MoreHorizontal,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const PAGE_SIZES = [10, 20, 25, 30, 40, 50];

interface DataTablePaginationProps<TData> {
  table: TableState<TData>;
}

export function DataTablePagination<TData>({
  table,
}: DataTablePaginationProps<TData>) {
  return (
    <div className="flex items-center justify-end px-2">
      {/* <div className="text-muted-foreground flex-1 text-sm">
        {table.getFilteredSelectedRowModel().rows.length} of{" "}
        {table.getFilteredRowModel().rows.length} row(s) selected.
      </div> */}
      <div className="flex items-center space-x-6 lg:space-x-8">
        <div className="flex items-center space-x-2">
          <p className="text-sm font-medium">Rows per page</p>
          <Select
            value={`${table.getState().pagination.pageSize}`}
            onValueChange={(value) => {
              table.setPageSize(Number(value));
            }}
          >
            <SelectTrigger className="h-8 w-[70px]">
              <SelectValue placeholder={table.getState().pagination.pageSize} />
            </SelectTrigger>
            <SelectContent side="top">
              {PAGE_SIZES.map((pageSize) => (
                <SelectItem key={pageSize} value={`${pageSize}`}>
                  {pageSize}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex w-[100px] items-center justify-center text-sm font-medium">
          Page {table.getState().pagination.pageIndex + 1} of{" "}
          {table.getPageCount()}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            className="hidden size-8 lg:flex"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">Go to first page</span>
            <ChevronsLeft />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">Go to previous page</span>
            <ChevronLeft />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <span className="sr-only">Go to next page</span>
            <ChevronRight />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="hidden size-8 lg:flex"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
          >
            <span className="sr-only">Go to last page</span>
            <ChevronsRight />
          </Button>
        </div>
      </div>
    </div>
  );
}

interface RowActionItem {
  type: "item";
  label: string;
  onClick: (row: any) => void;
}

interface RowActionMenu {
  type: "menu";
  label: string;
  children?: RowActionItem[];
}

type RowAction = RowActionItem | RowActionMenu;

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  pagination?: boolean;
  defaultPageSize?: number;
  className: string;
  onRowSelectionListener?: (rows: TData[]) => void;
  rowActions?: RowAction[];
  themeResetClassName?: string;
}

function DataTable<TData, TValue>({
  columns,
  data,
  pagination = true,
  defaultPageSize = 25,
  className,
  onRowSelectionListener,
  rowActions,
  themeResetClassName,
}: DataTableProps<TData, TValue>) {
  const [rowSelection, setRowSelection] = React.useState<RowSelectionState>({});

  const normalizedColumns = useColumnDefinitions(columns, {
    rowActions,
    themeResetClassName,
  });

  const table = useReactTable({
    data,
    columns: normalizedColumns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: pagination ? getPaginationRowModel() : undefined,
    onRowSelectionChange: setRowSelection,
    state: {
      rowSelection,
    },
    initialState: {
      pagination: {
        pageSize: defaultPageSize,
      },
    },
    enableMultiRowSelection: false,
  });

  React.useEffect(() => {
    onRowSelectionListener?.(
      table.getFilteredSelectedRowModel().rows.map((r) => r.original),
    );
  }, [table, rowSelection]);

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  onClick={row.getToggleSelectedHandler()}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={normalizedColumns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      {pagination && <DataTablePagination table={table} />}
    </div>
  );
}

function useColumnDefinitions<TData, TValue>(
  columns: ColumnDef<TData, TValue>[],
  options: { rowActions?: RowAction[]; themeResetClassName?: string },
) {
  const { rowActions, themeResetClassName } = options;
  return React.useMemo(() => {
    const normalizedColumns = [...columns];
    if (rowActions && rowActions.length > 0) {
      normalizedColumns.push({
        id: "__plasmic_actions",
        header: "Actions",
        cell: ({ row, column }) => (
          <>{...renderActions(row, column, rowActions)}</>
        ),
        meta: {
          className: themeResetClassName || "",
        },
      });
    }
    return normalizedColumns;
  }, [columns, rowActions, themeResetClassName]);
}

function renderActions<TData, TValue>(
  row: Row<TData>,
  column: Column<TData, TValue>,
  actions: RowAction[],
) {
  return actions.map((action) => {
    if (action.type === "item") {
      return (
        <a
          key={action.label}
          className={column.columnDef.meta?.className}
          style={{
            whiteSpace: "nowrap",
            cursor: "pointer",
          }}
          onClick={(e) => {
            e.stopPropagation();
            action.onClick?.(row.original);
          }}
        >
          {action.label}
        </a>
      );
    } else {
      return (
        <DropdownMenu key={action.label}>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>{action.label}</DropdownMenuLabel>
            {/* <DropdownMenuItem onClick={}>Copy payment ID</DropdownMenuItem> */}
            {action.children?.map((child) => (
              <DropdownMenuItem
                key={child.label}
                onClick={(e) => {
                  e.stopPropagation();
                  child.onClick?.(row.original);
                }}
              >
                {child.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      );
    }
  });
}

const DataTableMeta: CodeComponentMeta<DataTableProps<any, any>> = {
  name: "DataTable",
  description: "shadcn/ui DataTable component",
  props: {
    columns: {
      type: "array",
      description: "Column definitions for the table",
    },
    data: {
      type: "array",
      description: "Data to display in the table",
    },
    pagination: {
      type: "boolean",
      defaultValueHint: true,
    },
    defaultPageSize: {
      type: "choice",
      options: PAGE_SIZES,
      defaultValueHint: 25,
      hidden: (props) => props.pagination === false,
    },
    onRowSelectionListener: {
      type: "eventHandler",
      argTypes: [
        {
          name: "row",
          type: "object",
        },
      ],
    },
    rowActions: {
      type: "array",
      displayName: "Row actions",
      advanced: true,
      itemType: {
        type: "object",
        nameFunc: (item) => item.label,
        fields: {
          type: {
            type: "choice",
            options: ["item", "menu"],
            defaultValue: "item",
          },
          label: {
            type: "string",
            displayName: "Action label",
          },
          children: {
            type: "array",
            displayName: "Menu items",
            itemType: {
              type: "object",
              fields: {
                label: {
                  type: "string",
                  displayName: "Action label",
                },
                onClick: {
                  type: "eventHandler",
                  argTypes: [{ name: "row", type: "object" }],
                },
              },
            },
            hidden: (_ps, _ctx, { item }) => item.type !== "menu",
          },
          onClick: {
            type: "eventHandler",
            displayName: "Action",
            argTypes: [{ name: "row", type: "object" }],
            hidden: (_ps, _ctx, { item }) => item.type !== "item",
          },
        },
      },
    },
    themeResetClassName: {
      type: "themeResetClass",
      targetAllTags: true,
    },
  },
  states: {
    rowSelection: {
      type: "readonly",
      variableType: "object",
      onChangeProp: "onRowSelectionListener",
    },
  },
};

export { DataTable, DataTableMeta };

declare module "@tanstack/react-table" {
  // eslint-disable-next-line unused-imports/no-unused-vars
  interface ColumnMeta<TData extends RowData, TValue> {
    className?: string;
  }
}
