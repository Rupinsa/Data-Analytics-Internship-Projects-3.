
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "region_access.json"


def load_access_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_allowed_regions(user_role):
    config = load_access_config()

    if user_role not in config:
        raise PermissionError("Unknown demo user")

    return config[user_role]["allowed_regions"]


def check_region_access(user_role, region):
    allowed_regions = get_allowed_regions(user_role)

    return region in allowed_regions


def filter_by_region(dataframe, user_role, region_column="Region"):
    allowed_regions = get_allowed_regions(user_role)

    return dataframe[
        dataframe[region_column].isin(allowed_regions)
    ].copy()
