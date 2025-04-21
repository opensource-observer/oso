import re
import typing as t

from sqlmesh.core.linter.rule import Rule, RuleViolation
from sqlmesh.core.model import IncrementalByTimeRangeKind, Model, SqlModel

# Tables that indicate a model is related to projects (with canonical names)
PROJECT_TABLES = {
    "oso.int_artifacts_by_project",
    "oso.artifacts_by_project_v1",
    "oso.int_projects",
    "oso.projects_v1",
}

# Tables that indicate a model is related to collections (with canonical names)
COLLECTION_TABLES = {
    "oso.int_projects_by_collection",
    "oso.projects_by_collection_v1",
    "oso.int_collections",
    "oso.collections_v1",
}

PROJECT_ID_PATTERN = re.compile(r'\bproject_id\b', re.IGNORECASE)
COLLECTION_ID_PATTERN = re.compile(r'\bcollection_id\b', re.IGNORECASE)


class EntityCategoryTagRequired(Rule):
    """Models that reference project or collection tables must have the appropriate entity_category tags."""

    def check_model(self, model: Model) -> t.Optional[RuleViolation]:
        if not isinstance(model, SqlModel):
            return None

        # Check if the model has the required tags
        tags = model.tags or []
        has_project_tag = any(tag.startswith("entity_category=project") for tag in tags)
        has_collection_tag = any(tag.startswith("entity_category=collection") for tag in tags)

        # Get the model's dependencies
        dependencies = model.depends_on or []
        
        # Use the full canonical names from dependencies
        referenced_tables = {dep.lower() for dep in dependencies}

        # Check if the model references project or collection tables
        references_project = any(
            table in PROJECT_TABLES for table in referenced_tables
        )
        references_collection = any(
            table in COLLECTION_TABLES for table in referenced_tables
        )

        # If the model references project tables but doesn't have the project tag, report a violation
        if references_project and not has_project_tag:
            project_tables = [t for t in referenced_tables if t in PROJECT_TABLES]
            return self.violation(
                f"Model references project tables ({', '.join(project_tables)}) "
                f"but doesn't have the 'entity_category=project' tag."
            )

        # If the model references collection tables but doesn't have the collection tag, report a violation
        if references_collection and not has_collection_tag:
            collection_tables = [t for t in referenced_tables if t in COLLECTION_TABLES]
            return self.violation(
                f"Model references collection tables ({', '.join(collection_tables)}) "
                f"but doesn't have the 'entity_category=collection' tag."
            )

        # Additional check for incremental models that use project_id or collection_id
        is_incremental = isinstance(model.kind, IncrementalByTimeRangeKind)
        
        if is_incremental and isinstance(model, SqlModel) and model.query:
            query_str = str(model.query)
            
            # Check for project_id in incremental models
            if PROJECT_ID_PATTERN.search(query_str) and not has_project_tag:
                return self.violation(
                    "Incremental model uses 'project_id' but doesn't have the 'entity_category=project' tag."
                )
                
            # Check for collection_id in incremental models
            if COLLECTION_ID_PATTERN.search(query_str) and not has_collection_tag:
                return self.violation(
                    "Incremental model uses 'collection_id' but doesn't have the 'entity_category=collection' tag."
                )

        return None

    def violation(self, violation_msg: t.Optional[str] = None) -> RuleViolation:
        return RuleViolation(
            rule=self,
            violation_msg=violation_msg or "Models must have appropriate entity_category tags.",
        )
