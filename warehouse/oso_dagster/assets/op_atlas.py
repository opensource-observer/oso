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

# These are available but maybe shouldn't be included. It's enabled for now but
# we can decide if we find any data that shouldn't be made public.
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
            "defer_table_reflect": True,
        },
        {
            "table": "Badgeholder",
            "defer_table_reflect": True,
        },
        {
            "table": "Category",
            "defer_table_reflect": True,
        },
        {
            "table": "FundingReward",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "FundingRound",
            "defer_table_reflect": True,
        },
        {
            "table": "GithubProximity",
            "defer_table_reflect": True,
        },
        {
            "table": "ImpactStatement",
            "defer_table_reflect": True,
        },
        {
            "table": "ImpactStatementAnswer",
            "defer_table_reflect": True,
        },
        {
            "table": "Organization",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "OrganizationSnapshot",
            "incremental": incremental("createdAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "Project",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "ProjectContract",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "ProjectFunding",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "ProjectLinks",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "ProjectOrganization",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "ProjectRepository",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "ProjectSnapshot",
            "incremental": incremental("createdAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "PublishedContract",
            "defer_table_reflect": True,
        },
        {
            "table": "RewardClaim",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "User",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        # {
        #     "table": "UserAddress",
        #     "incremental": incremental("updatedAt"),
        #     "defer_table_reflect": True,
        # },
        #        {
        #            "table": "UserEmail",
        #            "defer_table_reflect": True,
        #        },
        #        {
        #            "table": "UserInteraction",
        #            "defer_table_reflect": True,
        #        },
        {
            "table": "UserOrganization",
            "incremental": incremental("updatedAt"),
            "defer_table_reflect": True,
        },
        {
            "table": "UserProjects",
            "defer_table_reflect": True,
        },
    ],
    pool_size=5,
    concurrency_key="op_atlas",
)
