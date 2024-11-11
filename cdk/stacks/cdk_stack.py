from aws_cdk import (
    Stack,
    TimeZone,
)
from constructs import Construct
from aws_cdk.aws_lambda_python_alpha import PythonFunction
import aws_cdk.aws_scheduler_alpha as scheduler
import aws_cdk.aws_scheduler_targets_alpha as targets
from aws_cdk.aws_lambda import Runtime
import aws_cdk.aws_s3 as s3
import aws_cdk as cdk
import aws_cdk.aws_sns as sns
import aws_cdk.aws_stepfunctions as sfn
import aws_cdk.aws_stepfunctions_tasks as tasks
import aws_cdk.aws_iam as iam
from aws_lambda_powertools.utilities import parameters
import json

PROJECT_NAME = "readinglist2inoue-kobo-topics"


class Readinglist2InoueKoboTopicsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        output_bucket = s3.Bucket.from_bucket_name(
            self,
            "OutputBucket",
            parameters.get_parameter("/readinglist2inoue-kobo-topics/OutputBucketName"),  # type: ignore
        )
        notion_api_key = parameters.get_parameter("/readinglist2inoue-kobo-topics/NotionApiKey")  # type: ignore

        convert_readinglist2md_function = PythonFunction(
            self,
            "ConvertReadinglist2MdFunction",
            entry="../app/readinglist2md",
            index="readinglist2md/functions/convert_readinglist2md_function.py",
            handler="lambda_handler",
            function_name=f"{PROJECT_NAME}-ConvertReadinglist2MdFunction",
            runtime=Runtime.PYTHON_3_10,
            timeout=cdk.Duration.seconds(600),
            memory_size=512,
            environment={
                "POWERTOOLS_SERVICE_NAME": PROJECT_NAME,
                "NOTION_API_KEY": notion_api_key,
            },
        )

        output_bucket.grant_read(convert_readinglist2md_function)
        output_bucket.grant_write(convert_readinglist2md_function)

        success_topic = sns.Topic(
            self, "ConvertReadinglist2MdStateMachineSuccessNotification"
        )
        error_topic = sns.Topic(
            self, "ConvertReadinglist2MdStateMachineErrorNotification"
        )

        convert_readinglist2md_state_machine = sfn.StateMachine(
            self,
            "ConvertReadinglist2MdStateMachine",
            timeout=cdk.Duration.seconds(600),
            state_machine_name=f"{PROJECT_NAME}-ConvertReadinglist2MdStateMachine",
            definition=sfn.Pass(
                self,
                "Pass",
            )
            .next(
                tasks.LambdaInvoke(
                    self,
                    "ConvertReadinglist2Md Step",
                    lambda_function=convert_readinglist2md_function,  # type: ignore
                    payload=sfn.TaskInput.from_object(
                        {
                            "output_s3_bucket": output_bucket.bucket_name,
                            "database_id": parameters.get_parameter("/readinglist2inoue-kobo-topics/NotionDatabaseId"),  # type: ignore,
                            "target_datetime": sfn.JsonPath.string_at(
                                "$.target_datetime"
                            ),
                            "window_days": sfn.JsonPath.string_at("$.window_days"),
                        }
                    ),
                ).add_catch(
                    tasks.SnsPublish(
                        self,
                        "Error Notification",
                        topic=error_topic,  # type: ignore
                        subject=f"AWS Account: {self.account}, リーディングリストをHugoで構成しているINOUE-KOBOトピックに変換する処理が失敗しました",
                        message=sfn.TaskInput.from_text(
                            "リーディングリストをHugoで構成しているINOUE-KOBOトピックに変換する処理が失敗しました。"
                        ),
                    ).next(sfn.Fail(self, "Error"))
                )
            )
            .next(
                tasks.SnsPublish(
                    self,
                    "Success Notification",
                    topic=success_topic,  # type: ignore
                    subject=f"AWS Account: {self.account}, リーディングリストをHugoで構成しているINOUE-KOBOトピックに変換する処理が成功しました",
                    message=sfn.TaskInput.from_text(
                        "リーディングリストをHugoで構成しているINOUE-KOBOトピックに変換する処理が成功しました。"
                    ),
                ).next(sfn.Succeed(self, "Success"))
            ),
        )

        # Scheduler
        target = targets.StepFunctionsStartExecution(
            state_machine=convert_readinglist2md_state_machine,
            input=scheduler.ScheduleTargetInput.from_object(
                {
                    "target_datetime": "<aws.scheduler.scheduled-time>",
                    "window_days": "7",
                }
            ),
        )

        schedule = scheduler.Schedule(
            self,
            "Scheduler",
            schedule=scheduler.ScheduleExpression.cron(
                minute="15", hour="00", week_day="TUE", time_zone=TimeZone.ASIA_TOKYO
            ),
            target=target,  # type: ignore
        )
