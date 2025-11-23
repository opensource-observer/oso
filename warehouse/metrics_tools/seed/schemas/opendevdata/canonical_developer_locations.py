from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class CanonicalDeveloperLocations(BaseModel):
    """Seed model for opendevdata canonical_developer_locations"""

    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    input: str | None = Column("VARCHAR", description="input")
    country: str | None = Column("VARCHAR", description="country")
    admin_level_1: str | None = Column("VARCHAR", description="admin level 1")
    admin_level_2: str | None = Column("VARCHAR", description="admin level 2")
    locality: str | None = Column("VARCHAR", description="locality")
    sublocality: str | None = Column("VARCHAR", description="sublocality")
    formatted_address: str | None = Column("VARCHAR", description="formatted address")
    lat: float | None = Column("DOUBLE", description="lat")
    lng: float | None = Column("DOUBLE", description="lng")
    raw: str | None = Column("VARCHAR", description="raw")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="canonical_developer_locations",
    base=CanonicalDeveloperLocations,
    rows=[
        CanonicalDeveloperLocations(
            canonical_developer_id=2468322,
            created_at=datetime.fromisoformat("2025-07-22 05:03:09"),
            input="Meerut U.P India ",
            country="India",
            admin_level_1="Uttar Pradesh",
            admin_level_2="Meerut Division",
            locality="Meerut",
            sublocality=None,
            formatted_address="Meerut, Uttar Pradesh, India",
            lat=28.9844618,
            lng=77.7064137,
            raw='{"results": [{"place": "//places.googleapis.com/places/ChIJJWO2V_RkDDkRXr6mhzOo-kI", "types": ["locality", "political"], "bounds": {"low": {"latitude": 28.901871300000003, "longitude": 77.62141230000002}, "high": {"latitude": 29.072653100000004, "longitude": 77.7765083}}, "placeId": "ChIJJWO2V_RkDDkRXr6mhzOo-kI", "location": {"latitude": 28.9844618, "longitude": 77.7064137}, "viewport": {"low": {"latitude": 28.901871300000003, "longitude": 77.62141230000002}, "high": {"latitude": 29.072653100000004, "longitude": 77.7765083}}, "granularity": "APPROXIMATE", "formattedAddress": "Meerut, Uttar Pradesh, India", "addressComponents": [{"types": ["locality", "political"], "longText": "Meerut", "shortText": "Meerut", "languageCode": "en"}, {"types": ["administrative_area_level_3", "political"], "longText": "Meerut", "shortText": "Meerut", "languageCode": "en"}, {"types": ["administrative_area_level_2", "political"], "longText": "Meerut Division", "shortText": "Meerut Division", "languageCode": "en"}, {"types": ["administrative_area_level_1", "political"], "longText": "Uttar Pradesh", "shortText": "UP", "languageCode": "en"}, {"types": ["country", "political"], "longText": "India", "shortText": "IN", "languageCode": "en"}]}]}',
        ),
        CanonicalDeveloperLocations(
            canonical_developer_id=2468316,
            created_at=datetime.fromisoformat("2025-07-22 05:03:09"),
            input="Tallinn",
            country="Estonia",
            admin_level_1="Harju County",
            admin_level_2=None,
            locality="Tallinn",
            sublocality=None,
            formatted_address="Tallinn, Estonia",
            lat=59.43696079999999,
            lng=24.7535746,
            raw='{"results": [{"place": "//places.googleapis.com/places/ChIJvxZW35mUkkYRcGL8GG2zAAQ", "types": ["locality", "political"], "bounds": {"low": {"latitude": 59.3518008, "longitude": 24.5501939}, "high": {"latitude": 59.591576999999994, "longitude": 24.9262838}}, "placeId": "ChIJvxZW35mUkkYRcGL8GG2zAAQ", "location": {"latitude": 59.43696079999999, "longitude": 24.7535746}, "viewport": {"low": {"latitude": 59.3518008, "longitude": 24.5501939}, "high": {"latitude": 59.591576999999994, "longitude": 24.9262838}}, "granularity": "APPROXIMATE", "formattedAddress": "Tallinn, Estonia", "addressComponents": [{"types": ["locality", "political"], "longText": "Tallinn", "shortText": "Tallinn", "languageCode": "en"}, {"types": ["administrative_area_level_1", "political"], "longText": "Harju County", "shortText": "Harju County", "languageCode": "en"}, {"types": ["country", "political"], "longText": "Estonia", "shortText": "EE", "languageCode": "en"}]}]}',
        ),
        CanonicalDeveloperLocations(
            canonical_developer_id=2468296,
            created_at=datetime.fromisoformat("2025-07-22 05:03:09"),
            input="Amsterdam, Netherlands",
            country="Netherlands",
            admin_level_1="North Holland",
            admin_level_2="Government of Amsterdam",
            locality="Amsterdam",
            sublocality=None,
            formatted_address="Amsterdam, Netherlands",
            lat=52.3675734,
            lng=4.9041388999999995,
            raw='{"results": [{"place": "//places.googleapis.com/places/ChIJVXealLU_xkcRja_At0z9AGY", "types": ["locality", "political"], "bounds": {"low": {"latitude": 52.278174, "longitude": 4.7287589}, "high": {"latitude": 52.431157299999995, "longitude": 5.0791619}}, "placeId": "ChIJVXealLU_xkcRja_At0z9AGY", "location": {"latitude": 52.3675734, "longitude": 4.9041388999999995}, "viewport": {"low": {"latitude": 52.278174, "longitude": 4.586594799999999}, "high": {"latitude": 52.4624825, "longitude": 5.0791619}}, "granularity": "APPROXIMATE", "formattedAddress": "Amsterdam, Netherlands", "addressComponents": [{"types": ["locality", "political"], "longText": "Amsterdam", "shortText": "Amsterdam", "languageCode": "en"}, {"types": ["administrative_area_level_2", "political"], "longText": "Government of Amsterdam", "shortText": "Government of Amsterdam", "languageCode": "en"}, {"types": ["administrative_area_level_1", "political"], "longText": "North Holland", "shortText": "NH", "languageCode": "en"}, {"types": ["country", "political"], "longText": "Netherlands", "shortText": "NL", "languageCode": "en"}]}]}',
        ),
        CanonicalDeveloperLocations(
            canonical_developer_id=2468297,
            created_at=datetime.fromisoformat("2025-07-22 05:03:09"),
            input="Remote",
            country=None,
            admin_level_1=None,
            admin_level_2=None,
            locality=None,
            sublocality=None,
            formatted_address=None,
            lat=None,
            lng=None,
            raw="{}",
        ),
        CanonicalDeveloperLocations(
            canonical_developer_id=2468336,
            created_at=datetime.fromisoformat("2025-07-22 05:03:09"),
            input="Buenos Aires, Argentina",
            country="Argentina",
            admin_level_1="Buenos Aires",
            admin_level_2=None,
            locality="Buenos Aires",
            sublocality=None,
            formatted_address="Buenos Aires, Argentina",
            lat=-34.6036739,
            lng=-58.3821215,
            raw='{"results": [{"place": "//places.googleapis.com/places/ChIJvQz5TjvKvJURh47oiC6Bs6A", "types": ["locality", "political"], "bounds": {"low": {"latitude": -34.7051011, "longitude": -58.5314522}, "high": {"latitude": -34.5265464, "longitude": -58.33514470000001}}, "placeId": "ChIJvQz5TjvKvJURh47oiC6Bs6A", "location": {"latitude": -34.6036739, "longitude": -58.3821215}, "viewport": {"low": {"latitude": -34.7051011, "longitude": -58.5314522}, "high": {"latitude": -34.5265464, "longitude": -58.33514470000001}}, "granularity": "APPROXIMATE", "formattedAddress": "Buenos Aires, Argentina", "addressComponents": [{"types": ["locality", "political"], "longText": "Buenos Aires", "shortText": "CABA", "languageCode": "en"}, {"types": ["administrative_area_level_1", "political"], "longText": "Buenos Aires", "shortText": "Buenos Aires", "languageCode": "en"}, {"types": ["country", "political"], "longText": "Argentina", "shortText": "AR", "languageCode": "en"}]}]}',
        ),
    ],
)
