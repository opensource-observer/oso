from datetime import datetime
from unittest import TestCase

from pyoso.analytics import DataAnalytics, DataStatus, MaterializationStatus


class TestDataAnalytics(TestCase):
    """Test cases for DataAnalytics functionality."""

    def test_root_keys_property(self):
        """Test the root_keys property functionality."""

        # Create analytics data with clear dependency hierarchy
        analytics_dict = {
            "root1": DataStatus(
                key="root1",
                status=MaterializationStatus(
                    latest_materialization=datetime.fromtimestamp(1642678800)
                ),
                dependencies=["child1", "child2"],
            ),
            "root2": DataStatus(
                key="root2",
                status=MaterializationStatus(
                    latest_materialization=datetime.fromtimestamp(1642678800)
                ),
                dependencies=["child3"],
            ),
            "child1": DataStatus(
                key="child1",
                status=MaterializationStatus(
                    latest_materialization=datetime.fromtimestamp(1642678800)
                ),
                dependencies=["grandchild1"],
            ),
            "child2": DataStatus(
                key="child2",
                status=MaterializationStatus(
                    latest_materialization=datetime.fromtimestamp(1642678800)
                ),
                dependencies=[],
            ),
            "child3": DataStatus(
                key="child3",
                status=MaterializationStatus(
                    latest_materialization=datetime.fromtimestamp(1642678800)
                ),
                dependencies=[],
            ),
            "grandchild1": DataStatus(
                key="grandchild1",
                status=MaterializationStatus(
                    latest_materialization=datetime.fromtimestamp(1642678800)
                ),
                dependencies=[],
            ),
        }

        analytics = DataAnalytics(analytics_dict)

        # Test root keys identification
        root_keys = analytics.root_keys
        self.assertEqual(set(root_keys), {"root1", "root2"})
        self.assertEqual(len(analytics), 6)

        # Test container functionality
        self.assertIn("root1", analytics)
        self.assertNotIn("nonexistent", analytics)

        # Test get method
        root1_data = analytics.get("root1")
        assert root1_data is not None
        self.assertEqual(root1_data.key, "root1")

        nonexistent_data = analytics.get("nonexistent")
        self.assertIsNone(nonexistent_data)

    def test_empty_analytics(self):
        """Test DataAnalytics with empty data."""
        analytics = DataAnalytics({})

        self.assertEqual(len(analytics), 0)
        self.assertEqual(analytics.root_keys, [])
        self.assertNotIn("anything", analytics)
