# like project's contract that declares every input the infrastructure expects without assinging ACTUAL VALUES

variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "tutor_email" {
  description = "Your email address"
  type        = string
}

variable "students" {
  description = "List of students to onboard"
  type = list(object({
    name          = string
    email         = string
    subject       = string
    session_day   = string
    session_time  = string
    reminder_day  = string
    reminder_time = string
    zoom_link     = optional(string)
  }))

}
