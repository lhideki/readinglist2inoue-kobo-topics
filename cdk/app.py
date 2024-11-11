#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.cdk_stack import Readinglist2InoueKoboTopicsStack


app = cdk.App()
stack = Readinglist2InoueKoboTopicsStack(
    app,
    "readinglist2inoue-kobo-topics",
)

cdk.Tags.of(stack).add("project-name", "readinglist2inoue-kobo-topics")

app.synth()
