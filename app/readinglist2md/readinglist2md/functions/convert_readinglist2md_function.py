from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from datetime import datetime, timedelta
import argparse
from readinglist2md import convert_readinglist2md
from readinglist2md import generate_index
import boto3

logger = Logger()


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    output_s3_bucket = event["output_s3_bucket"]
    database_id = event["database_id"]
    target_datetime = datetime.strptime(event["target_datetime"], "%Y-%m-%dT%H:%M:%SZ")
    window_days = event["window_days"]
    from_datetime = target_datetime - timedelta(days=int(window_days))

    markdown_str = convert_readinglist2md.convert_readinglist2md(
        database_id, from_datetime
    )

    if len(markdown_str) == 0:
        return

    from_date_str = from_datetime.strftime("%Y-%m-%d")

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=output_s3_bucket,
        Key=f"topics/topics/{from_date_str}/index.md",
        Body=markdown_str,
        ContentType="text/markdown",
    )

    generate_index.generate_index(output_s3_bucket)


if __name__ == "__main__":
    # テスト実行用のコードです。
    # cd app/readinglist2md
    # PYTHONPATH=. python readinglist2md/functions/convert_readinglist2md_function.py --output-s3-bucket "www.inoue-kobo.com" --database-id "NOTION_DATABASE_ID" --target-datetime "2024-11-09T15:00:00.000Z" --window-days 7
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-s3-bucket", required=True)
    parser.add_argument("--database-id", required=True)
    parser.add_argument("--target-datetime", required=True)
    parser.add_argument("--window-days", required=True)
    args = parser.parse_args()

    lambda_handler(
        {
            "output_s3_bucket": args.output_s3_bucket,
            "database_id": args.database_id,
            "target_datetime": args.target_datetime,
            "window_days": args.window_days,
        },
        type(
            "LambdaContext",
            (object,),
            {
                "function_name": "convert_readinglist2md_function",
                "memory_limit_in_mb": 128,
                "invoked_function_arn": "arn:aws:lambda:ap-northeast-1:123456789012:function:test_function",
                "aws_request_id": "test_request_id",
            },
        )(),  # type: ignore
    )
