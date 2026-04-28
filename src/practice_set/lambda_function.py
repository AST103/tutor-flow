# read student data from event payload

# query database for student history

# call bedrock to generate practice questions

# write practice questions to database

# send email via SES

import os
import json
import html
import re
import time
import random
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError

# initialize AWS clients
dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses", region_name=os.environ["AWS_REGION_NAME"])
bedrock = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION_NAME"])


_SUPERSCRIPT_DIGITS = str.maketrans(
    {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "-": "⁻",
    }
)


def to_unicode_superscripts(text: str) -> str:
    # Convert occurrences like x^2 or 10^-3 into x² / 10⁻³.
    # Keeps it intentionally simple for email readability.
    def _repl(match: re.Match[str]) -> str:
        exponent = match.group(1)
        return exponent.translate(_SUPERSCRIPT_DIGITS)

    return re.sub(r"\^(-?\d+)", _repl, text)


def get_latest_session_notes(table):

    try:
        response = table.query(
            KeyConditionExpression=Key("record_type").eq("session_notes"),
            ScanIndexForward=False,  # get latest first
            Limit=1,
        )
        items = response.get("Items", [])
        return items[0] if items else None

    except Exception as e:
        print(f"Error querying session notes from database: {str(e)}")
        return None


def generate_practice_set(student_name, student_subject, session_notes):
    # call Bedrock to generate practice questions based on session notes

    transient_error_codes = {
        "ThrottlingException",
        "TooManyRequestsException",
        "ModelTimeoutException",
        "TimeoutException",
        "ServiceUnavailableException",
    }

    try:
        if session_notes:
            prompt = f"""You are an expert tutor. Generate exactly 5 practice problems for a student.

Student: {student_name}
Subject: {student_subject}
Topics covered in last session: {session_notes.get("topics_covered", "general topics")}
Student struggled with: {session_notes.get("struggled_with", "nothing specific")}
Additional notes: {session_notes.get("notes", "no additional notes")}

Generate 5 targeted practice problems based on what the student struggled with.

Output rules (important):
- Output PLAIN TEXT only (no Markdown, no LaTeX, no $$ delimiters, no code blocks).
- Write exponents using Unicode superscripts when possible (e.g., x², y³, 10³). If you can't, use caret notation like x^2.
- Each problem starts with "Problem N:" on its own line.
- Separate problems with a blank line.
- Do not include answers or solution steps.
"""

        else:
            prompt = f"""You are an expert tutor. Generate exactly 5 practice problems for a student.

Student: {student_name}
Subject: {student_subject}

Generate 5 general practice problems for this subject.

Output rules (important):
- Output PLAIN TEXT only (no Markdown, no LaTeX, no $$ delimiters, no code blocks).
- Write exponents using Unicode superscripts when possible (e.g., x², y³, 10³). If you can't, use caret notation like x^2.
- Each problem starts with "Problem N:" on its own line.
- Separate problems with a blank line.
- Do not include answers or solution steps.
"""

        max_attempts = 5
        base_delay_seconds = 0.5

        last_err: Exception | None = None
        response = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = bedrock.invoke_model(
                    modelId="global.anthropic.claude-haiku-4-5-20251001-v1:0",
                    body=json.dumps(
                        {
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 1000,
                            "messages": [{"role": "user", "content": prompt}],
                        }
                    ),
                )
                break
            except ClientError as e:
                last_err = e
                error_code = (
                    e.response.get("Error", {}).get("Code")
                    if hasattr(e, "response") and isinstance(e.response, dict)
                    else None
                )

                if attempt == max_attempts or error_code not in transient_error_codes:
                    raise

                delay = base_delay_seconds * (2 ** (attempt - 1))
                jitter = random.random() * 0.2
                print(
                    f"Bedrock retryable error ({error_code}) for {student_name}; "
                    f"attempt {attempt}/{max_attempts}, sleeping {delay + jitter:.2f}s"
                )
                time.sleep(delay + jitter)
            except BotoCoreError as e:
                last_err = e
                if attempt == max_attempts:
                    raise

                delay = base_delay_seconds * (2 ** (attempt - 1))
                jitter = random.random() * 0.2
                print(
                    f"Bedrock BotoCoreError for {student_name}; "
                    f"attempt {attempt}/{max_attempts}, sleeping {delay + jitter:.2f}s"
                )
                time.sleep(delay + jitter)

        if response is None:
            if last_err is not None:
                raise last_err
            raise RuntimeError("Bedrock invoke_model failed without an exception")

        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    except ClientError as e:
        error_code = (
            e.response.get("Error", {}).get("Code")
            if hasattr(e, "response") and isinstance(e.response, dict)
            else None
        )
        print(f"Bedrock ClientError ({error_code}): {str(e)}")
        raise

    except (BotoCoreError, Exception) as e:
        print(f"Error generating practice set with Bedrock: {str(e)}")
        raise


def save_practice_set(table, practice_set):
    try:
        table.put_item(
            Item={
                "record_type": "practice_set",
                "timestamp": datetime.utcnow().isoformat(),
                "content": practice_set,
            }
        )
    except Exception as e:
        print(f"Error saving practice set to database: {str(e)}")
        raise


def send_practice_email(student_name, student_email, student_subject, practice_set):
    # send practice set to student via email
    try:
        safe_practice_set = html.escape(practice_set).replace("\r\n", "\n").replace("\n", "<br/>")
        ses.send_email(
            Source=os.environ["TUTOR_EMAIL"],
            Destination={"ToAddresses": [student_email]},
            Message={
                "Subject": {"Data": f"{student_subject} Practice Problems"},
                "Body": {
                    "Html": {
                        "Data": f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2c3e50;">Hi {student_name}!</h2>
                            <p style="color: #555;">Here is your personalized practice set for this week in <strong>{student_subject}</strong>:</p>
                            <hr style="border: 1px solid #eee;"/>
                            <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; line-height: 2;">
                                {safe_practice_set}
                            </div>
                            <hr style="border: 1px solid #eee;"/>
                            <p style="color: #555; font-size: 14px;">Good luck, and let me know if you have any questions!</p>
                        </body>
                        </html>
                        """
                    }
                },
            },
        )

    except ses.exceptions.MessageRejected as e:
        print(
            f"SES MessageRejected for {student_name} <{student_email}>: {str(e)}"
        )
        raise
    except ses.exceptions.MailFromDomainNotVerifiedException as e:
        print(
            f"SES MailFromDomainNotVerifiedException for {student_name} <{student_email}>: {str(e)}"
        )
        raise
    except Exception as e:
        print(f"Error sending practice email to {student_name} <{student_email}>: {str(e)}")
        raise


def lambda_handler(event, context):
    # read student data from event payload
    student_name = event["student_name"]
    student_email = event["student_email"]
    student_subject = event["student_subject"]
    table_name = event["table_name"]

    print(f"Generating practice set for {student_name} in {student_subject}")

    try:
        # get latest session notes for student
        table = dynamodb.Table(table_name)
        session_notes = get_latest_session_notes(table)

        if session_notes:
            print(f"Found session notes for {student_name}")
        else:
            print(
                f"No session notes found for {student_name}, generating general practice set"
            )

        # generate practice set using Bedrock
        practice_set = generate_practice_set(
            student_name, student_subject, session_notes
        )

        practice_set = to_unicode_superscripts(practice_set)

        # save practice set to database (raise on failure)
        save_practice_set(table, practice_set)

        # send practice set to student via email (raise on failure)
        send_practice_email(student_name, student_email, student_subject, practice_set)
        print(f"Practice set email sent to {student_email}")

        return {
            "statusCode": 200,
            "body": json.dumps(f"Practice set generated and emailed to {student_name}"),
        }

    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        raise
