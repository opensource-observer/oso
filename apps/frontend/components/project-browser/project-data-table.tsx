import React from "react";

import { RawCollection, DataTableConfig, Collection } from "@/lib/data-table";
import { IProjectView } from "@/lib/projects";
import { DataTableFieldGrowth } from "@/components/project-browser/data-table/field-growth";
import { DataTableFieldProject } from "@/components/project-browser/data-table/field-project";
import { DataTableFieldStatus } from "@/components/project-browser/data-table/field-status";
import { DataTable } from "@/components/project-browser/data-table/generic-data-table";
import { ExpandedProjectDataTable } from "@/components/project-browser/expanded-project-data-table";

export interface ProjectDataTableProps {
  className?: string;
  renderWithTestData?: boolean;
  data: Collection<IProjectView>;
  testData?: RawCollection;
  sortAsc?: boolean;
  onSortingChange?: (fieldName: string) => void;
}

export function ProjectDataTable(props: ProjectDataTableProps) {
  const { className } = props;
  const config: DataTableConfig = {
    fieldOrder: [
      "project",
      "status",
      "dependents",
      "activeDevs",
      "devReach",
      "opMaus",
      "opMausReach",
    ],
    fields: {
      project: {
        name: "project",
        type: "project",
        label: "Project",
        sortable: true,
        expandable: false,
        minWidth: 100,
      },
      status: {
        name: "status",
        type: "status",
        label: "Status",
        sortable: true,
        expandable: false,
        minWidth: 60,
      },
      dependents: {
        name: "dependents",
        type: "number",
        label: "Dependent Projects",
        sortable: true,
        expandable: false,
        textAlign: "right",
      },
      activeDevs: {
        name: "activeDevs",
        type: "growth",
        label: "Active Devs (Growth)",
        sortable: true,
        expandable: false,
        textAlign: "right",
      },
      devReach: {
        name: "devReach",
        type: "growth",
        label: "Downstream Devs (Growth)",
        sortable: true,
        expandable: true,
        expandableCb: (data: IProjectView) => {
          return data.hasDependents || false;
        },
        textAlign: "right",
      },
      opMaus: {
        name: "opMaus",
        type: "growth",
        label: "Onchain Users (Growth)",
        sortable: true,
        expandable: false,
        textAlign: "right",
      },
      opMausReach: {
        name: "opMausReach",
        type: "growth",
        label: "Downstream Users (Growth)",
        sortable: true,
        expandable: true,
        expandableCb: (data: IProjectView) => {
          return data.hasDependents || false;
        },
        textAlign: "right",
      },
    },
    types: {
      growth: {
        cellComponent: DataTableFieldGrowth,
      },
      project: {
        cellComponent: DataTableFieldProject,
      },
      status: {
        cellComponent: DataTableFieldStatus,
      },
    },
  };

  return (
    <div className={className}>
      <DataTable config={config} {...props}>
        <ExpandedProjectDataTable></ExpandedProjectDataTable>
      </DataTable>
    </div>
  );
}
