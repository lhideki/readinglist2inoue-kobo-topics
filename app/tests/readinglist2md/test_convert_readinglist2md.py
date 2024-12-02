import pytest
from readinglist2md import convert_readinglist2md
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

load_dotenv(verbose=True)


def test_convert_readinglist2md():
    database_id = str(os.getenv("NOTION_DATABASE_ID"))
    to_date = datetime.strptime(
        "2024-12-02T00:00:00.000Z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    )
    from_date = to_date - timedelta(days=2)

    markdown_str = convert_readinglist2md.convert_readinglist2md(
        database_id, from_date, to_date
    )

    print("\n")
    print(markdown_str)
