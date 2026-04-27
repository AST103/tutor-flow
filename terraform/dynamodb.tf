# creates one table PER student automatically.
# onboard a student, run tofu apply, and their taple appears

resource "aws_dynamodb_table" "student_tables" {
  for_each = { for student in var.students : student.name => student }

  name         = "tutorflow-${lower(replace(each.key, " ", "-"))}" #replaces table name to be tutorflow-first-last
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "record_type"
  range_key    = "timestamp"

  attribute {
    name = "record_type"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

}

resource "aws_dynamodb_table" "student_roster" {
  name         = "tutorflow-student-roster"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "student_name"

  attribute {
    name = "student_name"
    type = "S"
  }
}