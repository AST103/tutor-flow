# creates the HTTP endpoint that frontend calls

resource "aws_api_gateway_rest_api" "tutorflow_api" {
  name        = "tutorflow-api"
  description = "API for TutorFlow application"
}

# /students resource
resource "aws_api_gateway_resource" "students" {
  rest_api_id = aws_api_gateway_rest_api.tutorflow_api.id
  parent_id   = aws_api_gateway_rest_api.tutorflow_api.root_resource_id
  path_part   = "students"
}

# /log-session resource
resource "aws_api_gateway_resource" "log_session" {
  rest_api_id = aws_api_gateway_rest_api.tutorflow_api.id
  parent_id   = aws_api_gateway_rest_api.tutorflow_api.root_resource_id
  path_part   = "log-session"
}

# GET method for /students
resource "aws_api_gateway_method" "get_students" {
  rest_api_id   = aws_api_gateway_rest_api.tutorflow_api.id
  resource_id   = aws_api_gateway_resource.students.id
  http_method   = "GET"
  authorization = "NONE"
}

# OPTIONS method for /students (CORS preflight)
resource "aws_api_gateway_method" "options_students" {
  rest_api_id   = aws_api_gateway_rest_api.tutorflow_api.id
  resource_id   = aws_api_gateway_resource.students.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# POST method for /log-session
resource "aws_api_gateway_method" "post_log_session" {
  rest_api_id   = aws_api_gateway_rest_api.tutorflow_api.id
  resource_id   = aws_api_gateway_resource.log_session.id
  http_method   = "POST"
  authorization = "NONE"
}

# OPTIONS method for /log-session (CORS preflight)
resource "aws_api_gateway_method" "options_log_session" {
  rest_api_id   = aws_api_gateway_rest_api.tutorflow_api.id
  resource_id   = aws_api_gateway_resource.log_session.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# connect GET /students to Lambda
resource "aws_api_gateway_integration" "get_students" {
  rest_api_id             = aws_api_gateway_rest_api.tutorflow_api.id
  resource_id             = aws_api_gateway_resource.students.id
  http_method             = aws_api_gateway_method.get_students.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# connect OPTIONS /students to Lambda
resource "aws_api_gateway_integration" "options_students" {
  rest_api_id             = aws_api_gateway_rest_api.tutorflow_api.id
  resource_id             = aws_api_gateway_resource.students.id
  http_method             = aws_api_gateway_method.options_students.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# connect POST /log-session to Lambda
resource "aws_api_gateway_integration" "post_log_session" {
  rest_api_id             = aws_api_gateway_rest_api.tutorflow_api.id
  resource_id             = aws_api_gateway_resource.log_session.id
  http_method             = aws_api_gateway_method.post_log_session.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# connect OPTIONS /log-session to Lambda
resource "aws_api_gateway_integration" "options_log_session" {
  rest_api_id             = aws_api_gateway_rest_api.tutorflow_api.id
  resource_id             = aws_api_gateway_resource.log_session.id
  http_method             = aws_api_gateway_method.options_log_session.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

# deploy API
resource "aws_api_gateway_deployment" "tutorflow_api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.tutorflow_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.tutorflow_api,
      aws_api_gateway_resource.students,
      aws_api_gateway_resource.log_session,
      aws_api_gateway_method.get_students,
      aws_api_gateway_method.options_students,
      aws_api_gateway_method.post_log_session,
      aws_api_gateway_method.options_log_session,
      aws_api_gateway_integration.get_students,
      aws_api_gateway_integration.options_students,
      aws_api_gateway_integration.post_log_session,
      aws_api_gateway_integration.options_log_session,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.get_students,
    aws_api_gateway_integration.options_students,
    aws_api_gateway_integration.post_log_session,
    aws_api_gateway_integration.options_log_session,
  ]
}

# prod stage
resource "aws_api_gateway_stage" "prod" {
  stage_name    = "prod"
  rest_api_id   = aws_api_gateway_rest_api.tutorflow_api.id
  deployment_id = aws_api_gateway_deployment.tutorflow_api_deployment.id
}

# allow API Gateway to invoke Lambda
resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.tutorflow_api.execution_arn}/*/*"
}
