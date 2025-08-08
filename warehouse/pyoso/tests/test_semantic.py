import unittest

from pyoso.semantic import SemanticTableResponse


class TestMapToSemanticTableResponse(unittest.TestCase):
    def test_basic_table_mapping(self):
        """Test mapping a basic table with name and description only."""
        table_data = {"name": "users", "description": "User information table"}

        result = SemanticTableResponse.model_validate(table_data)

        self.assertEqual(result.name, "users")
        self.assertEqual(result.description, "User information table")
        self.assertEqual(len(result.columns), 0)
        self.assertEqual(len(result.relationships), 0)

    def test_complete_table_with_columns_and_relationships(self):
        """Test mapping a complete table with both columns and relationships."""
        table_data = {
            "name": "orders",
            "description": "Customer order information",
            "columns": [
                {"name": "id", "type": "bigint", "description": "Order ID"},
                {
                    "name": "user_id",
                    "type": "bigint",
                    "description": "Foreign key to users table",
                },
            ],
            "relationships": [
                {
                    "sourceColumn": "user_id",
                    "targetTable": "users",
                    "targetColumn": "id",
                }
            ],
        }

        result = SemanticTableResponse.model_validate(table_data)

        self.assertEqual(result.name, "orders")
        self.assertEqual(result.description, "Customer order information")

        # Check columns
        self.assertEqual(len(result.columns), 2)
        self.assertEqual(result.columns[0].name, "id")
        self.assertEqual(result.columns[0].type, "bigint")
        self.assertEqual(result.columns[0].description, "Order ID")

        self.assertEqual(result.columns[1].name, "user_id")
        self.assertEqual(result.columns[1].type, "bigint")
        self.assertEqual(result.columns[1].description, "Foreign key to users table")

        # Check relationships
        self.assertEqual(len(result.relationships), 1)
        self.assertEqual(result.relationships[0].source_column, "user_id")
        self.assertEqual(result.relationships[0].target_table, "users")
        self.assertEqual(result.relationships[0].target_column, "id")

    def test_missing_optional_fields(self):
        """Test mapping with missing optional fields defaults to empty strings."""
        table_data = {
            "name": "table",
            "description": None,
            "columns": [
                {
                    "name": "id",
                    "type": "",
                    "description": "",
                },  # Missing type and description (optional)
                {
                    "name": "status",
                    "type": "varchar",
                    "description": None,
                },  # Missing description (optional)
            ],
        }

        result = SemanticTableResponse.model_validate(table_data)

        # Missing table fields default to empty strings
        self.assertEqual(result.name, "table")
        self.assertEqual(result.description, None)

        # Check columns with missing optional fields default to empty strings
        self.assertEqual(len(result.columns), 2)
        self.assertEqual(result.columns[0].name, "id")
        self.assertEqual(result.columns[0].type, "")
        self.assertEqual(result.columns[0].description, "")

        self.assertEqual(result.columns[1].name, "status")
        self.assertEqual(result.columns[1].type, "varchar")
        self.assertEqual(result.columns[1].description, None)

        # No relationships in this test since all relationship fields are required
        self.assertEqual(len(result.relationships), 0)

    def test_return_type_and_structure(self):
        """Test that the function returns the correct type and handles minimal data."""
        # Test return type
        result = SemanticTableResponse.model_validate(
            {"name": "test", "description": None}
        )
        self.assertIsInstance(result, SemanticTableResponse)
        self.assertIsInstance(result.columns, list)
        self.assertIsInstance(result.relationships, list)

        # Test minimal data (just required name field)
        minimal_result = SemanticTableResponse.model_validate(
            {"name": "minimal_table", "description": None}
        )
        self.assertEqual(minimal_result.name, "minimal_table")
        self.assertEqual(minimal_result.description, None)
        self.assertEqual(len(minimal_result.columns), 0)
        self.assertEqual(len(minimal_result.relationships), 0)
