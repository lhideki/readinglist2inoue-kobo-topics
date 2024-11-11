from notion_client import Client
from datetime import datetime
from jinja2 import Template
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv(verbose=True)
notion = Client(auth=os.environ["NOTION_API_KEY"])


def _get_unshared_reading_list(database_id: str, from_date: datetime):
    response = notion.databases.query(
        **{
            "database_id": database_id,
        }
    )

    entries = []
    for page in response["results"]:  # type: ignore
        entry = {
            "名前": (
                page["properties"]["名前"]["title"][0]["text"]["content"]
                if page["properties"]["名前"]["title"]
                else None
            ),
            "AI 要約": (
                page["properties"]["AI 要約"]["rich_text"][0]["text"]["content"]
                if page["properties"]["AI 要約"]["rich_text"]
                else None
            ),
            "URL": page["properties"]["URL"]["url"],
            "既読": page["properties"]["既読"]["checkbox"],
            "カテゴリ": (
                page["properties"]["カテゴリ"]["select"]["name"]
                if page["properties"]["カテゴリ"]["select"]
                else None
            ),
            "タグ": [tag["name"] for tag in page["properties"]["タグ"]["multi_select"]],
            "作成日時": datetime.strptime(
                page["properties"]["作成日時"]["created_time"],
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ),
        }

        if entry["作成日時"] >= from_date:
            entries.append(entry)

    return entries


def convert_readinglist2md(database_id: str, from_date: datetime) -> str:
    unshared_reading_list = _get_unshared_reading_list(database_id, from_date)

    if len(unshared_reading_list) == 0:
        return ""

    unshared_reading_list_df = pd.DataFrame(unshared_reading_list)

    markdown_strs = []
    markdown_strs.append(
        f"""---
title: {from_date.strftime("%Y-%m-%d")} Topics
date: {from_date.strftime("%Y-%m-%d")}
toc: true
author: false
---

# {from_date.strftime("%Y-%m-%d")} Topics
"""
    )
    for i, group in enumerate(unshared_reading_list_df.groupby("カテゴリ")):
        category = group[0]
        entries = group[1]

        markdown_strs.append(f"\n## {category}\n")

        for entry in entries.to_dict(orient="records"):
            template = Template(
                """
### {{ entry['名前'] }}

* Tags: {{ ','.join(entry['タグ']) }}
* URL: {{ entry['URL'] }}

{{ entry['AI 要約'] }}

"""
            )
            markdown_strs.append(template.render(entry=entry))

    return "".join(markdown_strs)
