package trino_test

import data.trino

test_admin_user_allowed if {
	trino.allow with input as {"context": {
		"identity": {"user": "admin"},
		"softwareStack": {"trinoVersion": "434"},
	}}
	trino.allow with input as {"context": {
		"identity": {"user": "sqlmesh"},
		"softwareStack": {"trinoVersion": "434"},
	}}
	trino.allow with input as {"context": {
		"identity": {"user": "carl"},
		"softwareStack": {"trinoVersion": "434"},
	}}
}

test_allow_execute_query_allowed if {
	trino.allow with input as {
		"context": {
			"identity": {"user": "ro-orgname-orgid"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {"operation": "ExecuteQuery"},
	}
}

test_allow_public_catalog_allowed if {
	trino.allow with input as {
		"context": {
			"identity": {"user": "ro-orgname-orgid"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "SelectFromColumns",
			"resource": {"table": {
				"catalogName": "iceberg",
				"schemaName": "example_schema",
				"tableName": "example_table",
			}},
		},
	}
	trino.allow with input as {
		"context": {
			"identity": {"user": "ro-orgname-orgid"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "AccessCatalog",
			"resource": {"catalog": {"name": "iceberg"}},
		},
	}
}

test_allow_private_catalog_allowed if {
	trino.allow with input as {
		"context": {
			"identity": {"user": "ro-orgname-orgid"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "SelectFromColumns",
			"resource": {"table": {
				"catalogName": "orgname__catalog",
				"schemaName": "example_schema",
				"tableName": "example_table",
			}},
		},
	}
	trino.allow with input as {
		"context": {
			"identity": {"user": "ro-orgname-orgid"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "AccessCatalog",
			"resource": {"catalog": {"name": "orgname__catalog"}},
		},
	}
}

test_allow_private_catalog_denied if {
	not trino.allow with input as {
		"context": {
			"identity": {"user": "ro-orgname-orgid"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "SelectFromColumns",
			"resource": {"table": {
				"catalogName": "example_catalog",
				"schemaName": "example_schema",
				"tableName": "example_table",
			}},
		},
	}
}

test_allow_anonymous_denied if {
	not trino.allow with input as {"context": {
		"identity": {"user": ""},
		"softwareStack": {"trinoVersion": "434"},
	}}
}

test_allow_dynamic_catalog_denied_wrong_catalog if {
	not trino.allow with input as {
		"context": {
			"identity": {"user": "ro-orgname-orgid"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "SelectFromColumns",
			"resource": {"table": {
				"catalogName": "another-catalog",
				"schemaName": "some-id",
				"tableName": "example_table",
			}},
		},
	}
}

test_allow_reading_user_shared_catalog_allowed if {
	trino.allow with input as {
		"context": {
			"identity": {"user": "ro-orgname-orgid"},
			"softwareStack": {"trinoVersion": "434"},
		},
		"action": {
			"operation": "SelectFromColumns",
			"resource": {
				"table": {
					"catalogName": "user_shared",
					"schemaName": "org_orgid_datasetid",
					"tableName": "random_table",
					"columns": ["col1", "col2"]
				},
			},
		},
	}
}