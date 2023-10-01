from io import StringIO
from fastapi import HTTPException
from pydantic import BaseModel
from enum import Enum
import csv
import random
from datetime import date, timedelta
import pandas as pd
import numpy as np


CSV_EXAMPLE = {
    "num_entities": 10,
    "start_date": "2022-01-01",
    "test_date": "2022-02-01",
    "end_date": "2022-02-15",
    "values": [
        {
            "name": "Revenue",
            "units": "$",
            "min_value": 0,
            "max_value": 1000000,
            "skew_percent": 10.0,
        },
        {
            "name": "Units Sold",
            "units": "pc",
            "min_value": 0,
            "max_value": 1000,
            "skew_percent": 5.0,
        },
    ],
}

#  Could not use StrEnum for Units, due to SqlAlchemy version conflict, beware pitfall mentioned here
#  https://fastapi-utils.davidmontague.xyz/user-guide/basics/enums/


class Units(str, Enum):
    dollars = "$"
    units = "pc"
    # TODO: Examples of possible other units:
    # hours = "hrs"
    # score = "points"
    # percent = "%"


class Value(BaseModel):
    name: str
    units: Units
    min_value: int
    max_value: int
    skew_percent: float


class CSV(BaseModel):
    num_entities: int
    start_date: str
    test_date: str
    end_date: str
    values: list[Value]

    model_config = {"json_schema_extra": {"examples": [CSV_EXAMPLE]}}

class Buckets(BaseModel):
    names: list[str]
    counts: list[int]

class Operations(str, Enum):
    MINIMUM = 'min'
    MAXMUM = 'max'
    MEDIAN = 'median'
    AVERAGE = 'mean'
    TOTAL = 'sum'


def abbreviate_number(num, prefix='', suffix=''):
    for unit in ("", "K", "M", "B", "T"):
        if abs(num) < 1000.0:
            return f"{prefix}{num:3.1f}{unit}{suffix}"
        num /= 1000.0
    return f"{prefix}{num:.1f}{suffix}"


def distribute_data(csv_file, operation, entities, values, num_buckets):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Ensure the specified columns exist in the DataFrame
    if entities not in df.columns or values not in df.columns:
        raise ValueError("Specified columns not found in the CSV file")

    # Group by entities and calculate the median, mean, sum, etc. of 'values' for each entity
    aggregation_operation = f'df.groupby(entities)[values].{str(operation.value)}().reset_index()'
    entity_aggregations = eval(aggregation_operation)

    # Get the minimum and maximum medians
    min_median = entity_aggregations[values].min()
    max_median = entity_aggregations[values].max()

    # Calculate bin edges to equally separate the medians
    bin_edges = np.linspace(min_median, max_median, num_buckets + 1)

    # Create histogram data using pandas cut
    entity_aggregations['buckets'] = pd.cut(entity_aggregations[values], bins=bin_edges, include_lowest=True, right=True)

    # Count entities in each bucket
    distribution = entity_aggregations['buckets'].value_counts().sort_index()    # Prepare the data for plotting
    bucket_labels = [f'{abbreviate_number(bucket.left, "$")}-{abbreviate_number(bucket.right, "$")}' for bucket in distribution.index]
    counts = distribution.values

    return bucket_labels, counts

    # # Create a distribution chart using matplotlib
    # plt.figure(figsize=(10, 6))
    # plt.bar(bucket_labels, counts, align='center', alpha=0.7)labels
    # plt.xlabel('Buckets')
    # plt.ylabel('Count')labels
    # plt.title('Distribution Chart')
    # plt.xticks(rotation=45)
    # plt.tight_layout()

    # # Display or save the plot
    # plt.show()


def generate_site_names(num_sites: int):
    capitals_and_major_cities = [
        # Alabama
        "Montgomery",
        "Birmingham",
        # Alaska
        "Juneau",
        "Anchorage",
        # Arizona
        "Phoenix",
        "Tucson",
        # Arkansas
        "Little Rock",
        "Fort Smith",
        # California
        "Sacramento",
        "Los Angeles",
        # Colorado
        "Denver",
        "Colorado Springs",
        # Connecticut
        "Hartford",
        "Bridgeport",
        # Delaware
        "Dover",
        "Wilmington",
        # Florida
        "Tallahassee",
        "Jacksonville",
        # Georgia
        "Atlanta",
        "Augusta",
        # Hawaii
        "Honolulu",
        "Hilo",
        # Idaho
        "Boise",
        "Meridian",
        # Illinois
        "Springfield",
        "Chicago",
        # Indiana
        "Indianapolis",
        "Fort Wayne",
        # Iowa
        "Des Moines",
        "Cedar Rapids",
        # Kansas
        "Topeka",
        "Wichita",
        # Kentucky
        "Frankfort",
        "Louisville",
        # Louisiana
        "Baton Rouge",
        "New Orleans",
        # Maine
        "Augusta",
        "Portland",
        # Maryland
        "Annapolis",
        "Baltimore",
        # Massachusetts
        "Boston",
        "Worcester",
        # Michigan
        "Lansing",
        "Detroit",
        # Minnesota
        "Saint Paul",
        "Minneapolis",
        # Mississippi
        "Jackson",
        "Gulfport",
        # Missouri
        "Jefferson City",
        "Kansas City",
        # Montana
        "Helena",
        "Billings",
        # Nebraska
        "Lincoln",
        "Omaha",
        # Nevada
        "Carson City",
        "Las Vegas",
        # New Hampshire
        "Concord",
        "Manchester",
        # New Jersey
        "Trenton",
        "Newark",
        # New Mexico
        "Santa Fe",
        "Albuquerque",
        # New York
        "Albany",
        "New York City",
        # North Carolina
        "Raleigh",
        "Charlotte",
        # North Dakota
        "Bismarck",
        "Fargo",
        # Ohio
        "Columbus",
        "Cleveland",
        # Oklahoma
        "Oklahoma City",
        "Tulsa",
        # Oregon
        "Salem",
        "Portland",
        # Pennsylvania
        "Harrisburg",
        "Philadelphia",
        # Rhode Island
        "Providence",
        "Warwick",
        # South Carolina
        "Columbia",
        "Charleston",
        # South Dakota
        "Pierre",
        "Sioux Falls",
        # Tennessee
        "Nashville",
        "Memphis",
        # Texas
        "Austin",
        "Houston",
        # Utah
        "Salt Lake City",
        "West Valley City",
        # Vermont
        "Montpelier",
        "Burlington",
        # Virginia
        "Richmond",
        "Virginia Beach",
        # Washington
        "Olympia",
        "Seattle",
        # West Virginia
        "Charleston",
        "Huntington",
        # Wisconsin
        "Madison",
        "Milwaukee",
        # Wyoming
        "Cheyenne",
        "Casper",
    ]

    total_cities = len(capitals_and_major_cities)

    site_names = []

    for i in range(num_sites):
        if i < total_cities:
            site_names.append(capitals_and_major_cities[i])
        else:
            site_names.append(f"{capitals_and_major_cities[i % total_cities]}-{i}")

    return site_names


def generate_values(CSV, skew):
    values = {}
    for value in CSV.values:
        random_value = random.uniform(value.min_value, value.max_value)
        if skew:
            random_value += random_value * value.skew_percent / 100

        if value.units == Units.dollars:
            values[value.name] = round(random_value, 2)
        elif value.units == Units.units:
            values[value.name] = int(random_value)
        else:
            raise HTTPException(
                status_code=400, detail=f'Error: Unrecognized value "{value.name}"'
            )

    return values


def generate_period_rows(writer, CSV, site, role, start_date, end_date, skew=False):
    current_date = start_date
    while current_date <= end_date:
        writer.writerow(
            {"Site": site, "Role": role, "Date": current_date}
            | generate_values(CSV, skew)
        )
        current_date += timedelta(days=1)


def generate_csv(CSV):
    try:
        start_date = date.fromisoformat(CSV.start_date)
        test_date = date.fromisoformat(CSV.test_date)
        end_date = date.fromisoformat(CSV.end_date)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Error: Dates must be in the format 'YYYY-MM-DD'"
        )

    if not (start_date < test_date < end_date):
        raise HTTPException(
            status_code=400,
            detail="Dates must be in the order: start_date < test_date < end_date",
        )

    # Using in-memory StringIO in lieu of temporary disk file
    csvfile = StringIO()
    fieldnames = ["Site", "Role", "Date"] + [
        value.name for value in CSV.values
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()

    sites = generate_site_names(CSV.num_entities)
    for i, site in enumerate(sites):
        role = "Treatment" if i < len(sites) / 2 else "Control"
        if role == "Treatment":
            # Pre-treatment
            generate_period_rows(
                writer,
                CSV,
                site,
                role,
                start_date,
                test_date - timedelta(days=1),
            )
            # Test-treatment
            generate_period_rows(
                writer, CSV, site, role, test_date, end_date, True
            )
        else:
            # Pre-control
            generate_period_rows(
                writer,
                CSV,
                site,
                role,
                start_date,
                test_date - timedelta(days=1),
            )
            # Test-control
            generate_period_rows(
               writer, CSV, site, role, test_date, end_date
            )
    
    # Reset to beginning of the file for reading (in lieu of close and re-open an actual file)
    csvfile.seek(0)
    return csvfile
