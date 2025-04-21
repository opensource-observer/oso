import typing as t

from sqlmesh.core.linter.rule import Rule, RuleViolation
from sqlmesh.core.model import Model, SqlModel


class EntityCategoryTagRequired(Rule):
    """Models that reference project or collection tables must have the appropriate entity_category tags."""

    # Tables that indicate a model is related to projects
    PROJECT_TABLES = {
        "int_artifacts_by_project",
        "artifacts_by_project_v1",
        "int_projects",
        "projects_v1",
    }

    # Tables that indicate a model is related to collections
    COLLECTION_TABLES = {
        "int_projects_by_collection",
        "projects_by_collection_v1",
        "int_collections",
        "collections_v1",
    }

    def check_model(self, model: Model) -> t.Optional[RuleViolation]:
        if not isinstance(model, SqlModel):
            return None

        # Check if the model has the required tags
        tags = model.tags or []
        has_project_tag = any(tag.startswith("entity_category=project") for tag in tags)
        has_collection_tag = any(tag.startswith("entity_category=collection") for tag in tags)

        # Get the model's dependencies
        dependencies = model.depends_on or []
        
        # Extract just the table names from the dependencies
        referenced_tables = set()
        for dep in dependencies:
            # Dependencies are in the format "schema.table"
            if "." in dep:
                schema, table = dep.split(".", 1)
                referenced_tables.add(table.lower())
            else:
                referenced_tables.add(dep.lower())

        # Check if the model references project or collection tables
        references_project = any(
            table in self.PROJECT_TABLES for table in referenced_tables
        )
        references_collection = any(
            table in self.COLLECTION_TABLES for table in referenced_tables
        )

        # If the model references project tables but doesn't have the project tag, report a violation
        if references_project and not has_project_tag:
            project_tables = [t for t in referenced_tables if t in self.PROJECT_TABLES]
            return self.violation(
                f"Model references project tables ({', '.join(project_tables)}) "
                f"but doesn't have the 'entity_category=project' tag."
            )

        # If the model references collection tables but doesn't have the collection tag, report a violation
        if references_collection and not has_collection_tag:
            collection_tables = [t for t in referenced_tables if t in self.COLLECTION_TABLES]
            return self.violation(
                f"Model references collection tables ({', '.join(collection_tables)}) "
                f"but doesn't have the 'entity_category=collection' tag."
            )

        return None

    def violation(self, violation_msg: t.Optional[str] = None) -> RuleViolation:
        return RuleViolation(
            rule=self,
            violation_msg=violation_msg or "Models must have appropriate entity_category tags.",
        )
