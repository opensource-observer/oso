from dlt.sources import incremental
from oso_dagster.factories import sql_assets
from oso_dagster.utils import SecretReference

# The following tables should be included in the op_atlas asset:
# Application
# Badgeholder
# Category
# FundingReward (updatedAt)
# FundingRound
# GithubProximity
# ImpactStatement
# ImpactStatementAnswer
# Organization (updatedAt)
# OrganizationSnapshot (createdAt)
# Project (updatedAt)
# ProjectContract (updatedAt)
# ProjectFunding (updatedAt)
# ProjectLinks (updatedAt)
# ProjectOrganization (updatedAt)
# ProjectRepository (updatedAt)
# ProjectSnapshot (createdAt)
# RewardClaim (updatedAt)

# These are available but maybe shouldn't be included:
# User (updatedAt)
# UserAddress (updatedAt)
# UserEmail (no access)
# UserInteraction
# UserOrganization (updatedAt)
# UserProjects


op_atlas = sql_assets(
    "op_atlas",
    SecretReference(group_name="op_atlas", key="database"),
    [
        {
            "table": "Application",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "Badgeholder",
        },
        {
            "table": "Category",
        },
        {
            "table": "FundingReward",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "FundingRound",
        },
        {
            "table": "GithubProximity",
        },
        {
            "table": "ImpactStatement",
        },
        {
            "table": "ImpactStatementAnswer",
        },
        {
            "table": "Organization",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "OrganizationSnapshot",
            "incremental": incremental("createdAt"),
        },
        {
            "table": "Project",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "ProjectContract",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "ProjectFunding",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "ProjectLinks",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "ProjectOrganization",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "ProjectRepository",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "ProjectSnapshot",
            "incremental": incremental("createdAt"),
        },
        {
            "table": "RewardClaim",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "User",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "UserAddress",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "UserEmail",
        },
        {
            "table": "UserInteraction",
        },
        {
            "table": "UserOrganization",
            "incremental": incremental("updatedAt"),
        },
        {
            "table": "UserProjects",
        },
    ],
)
