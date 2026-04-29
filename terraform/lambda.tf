# create a zip file from lambda code
data "archive_file" "practice_set_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/practice_set/lambda_function.py"
  output_path = "${path.module}/practice_set.zip"
}

data "archive_file" "reminder_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/reminder/lambda_function.py"
  output_path = "${path.module}/reminder.zip"
}

# add a new lambda to populate our roster on deployment
data "archive_file" "roster_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/roster/lambda_function.py"
  output_path = "${path.module}/roster.zip"
}

# add a new lambda for api handler
data "archive_file" "api_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/api/lambda_function.py"
  output_path = "${path.module}/api.zip"
}

# create Lambda function for practice question generation
resource "aws_lambda_function" "practice_set" {
  function_name    = "tutorflow-processor-practice"
  filename         = data.archive_file.practice_set_zip.output_path
  source_code_hash = data.archive_file.practice_set_zip.output_base64sha256
  role             = aws_iam_role.practice_set_lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60 # longer time to call Bedrock
  memory_size      = 256

  environment { #specifies which student lambda function should look at
    variables = {
      TUTOR_EMAIL     = var.tutor_email
      AWS_REGION_NAME = var.aws_region
    }
  }
}

# create Lambda function for session reminders
resource "aws_lambda_function" "reminder" {
  function_name    = "tutorflow-processor-reminder"
  filename         = data.archive_file.reminder_zip.output_path
  source_code_hash = data.archive_file.reminder_zip.output_base64sha256
  role             = aws_iam_role.reminder_lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30 # just sending an email shorter time
  memory_size      = 128

  environment {
    variables = {
      TUTOR_EMAIL     = var.tutor_email
      AWS_REGION_NAME = var.aws_region
    }
  }
}

# create Lambda function to populate student roster
resource "aws_lambda_function" "roster_seeder" {
  function_name    = "tutorflow-processor-roster"
  filename         = data.archive_file.roster_zip.output_path
  source_code_hash = data.archive_file.roster_zip.output_base64sha256
  role             = aws_iam_role.roster_seeder_lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      AWS_REGION_NAME   = var.aws_region
      STUDENTS_JSON     = jsonencode(var.students)
      ROSTER_TABLE_NAME = aws_dynamodb_table.student_roster.name
    }
  }
}

# create Lambda function for API handler
resource "aws_lambda_function" "api_handler" {
  function_name    = "tutorflow-api-handler"
  filename         = data.archive_file.api_zip.output_path
  source_code_hash = data.archive_file.api_zip.output_base64sha256
  role             = aws_iam_role.api_handler_lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      AWS_REGION_NAME   = var.aws_region
      ROSTER_TABLE_NAME = aws_dynamodb_table.student_roster.name
    }
  }
}

# invoke seeder every time we deploy
resource "aws_lambda_invocation" "seed_roster" {
  function_name = aws_lambda_function.roster_seeder.function_name

  input = jsonencode({
    source = "terraform"
  })

  triggers = {
    students_hash = md5(jsonencode(var.students)) # re-run seeder if students list changes
    seeder_hash   = data.archive_file.roster_zip.output_base64sha256
  }

  depends_on = [
    aws_dynamodb_table.student_roster,
  ]
}
