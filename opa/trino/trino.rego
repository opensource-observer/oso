package trino

# If the user is in the format `jwt-<org_id>`, allow access if the catalog matches the org_id
# or if the catalog is "iceberg".
user := input.context.identity.user

allow if {
	startswith(user, "jwt-")
	org_id := substring(user, count("jwt-"), -1)

	# Check if catalog access is allowed based on org_id or if it's a public catalog
	catalog_access_permitted := startswith(input.action.resource.table.catalogName, org_id)
	public_catalog := input.action.resource.table.catalogName in {"iceberg"}

	some allowed in [public_catalog, catalog_access_permitted]
	allowed == true
}

# Allow access for admin and sqlmesh users.
allow if {
	user in {"admin", "sqlmesh"}
}
