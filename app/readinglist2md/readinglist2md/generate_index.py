import boto3
from datetime import datetime


def generate_index(topics_s3_bucket: str):
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    response_iterator = paginator.paginate(Bucket=topics_s3_bucket)

    markdown_strs = []
    markdown_strs.append(
        f"""---
title: Topics
date: {datetime.now().strftime("%Y-%m-%d")}
menu: main
toc: false
author: false
---

"""
    )
    for response in response_iterator:
        if "Contents" in response:
            for content in response["Contents"]:
                if content["Key"].endswith("index.md"):
                    key = content["Key"]
                    # Hugoが以下のようにindex.mdを抜いたパスを要求します。
                    # * topics/2024-11-09
                    content_path = "/".join(key.split("/")[2:-1])
                    markdown_strs.append(
                        f"* [{content['Key'].split('/')[2]}]({content_path})"
                    )

    markdown_str = "\n".join(markdown_strs)

    s3.put_object(
        Bucket=topics_s3_bucket,
        Key=f"topics/topics.md",
        Body=markdown_str,
        ContentType="text/markdown",
    )
