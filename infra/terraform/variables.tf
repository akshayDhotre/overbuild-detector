variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "overbuild-detector"
}

variable "aws_region" {
  description = "AWS region for ECS resources"
  type        = string
  default     = "us-east-1"
}

variable "container_image" {
  description = "Container image URI"
  type        = string
}

variable "execution_role_arn" {
  description = "ECS execution role ARN"
  type        = string
}

variable "task_role_arn" {
  description = "ECS task role ARN"
  type        = string
}

variable "subnet_ids" {
  description = "Subnets for Fargate service"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security groups for Fargate service"
  type        = list(string)
}

variable "desired_count" {
  description = "ECS service desired count"
  type        = number
  default     = 1
}

variable "task_cpu" {
  description = "Task CPU units"
  type        = string
  default     = "256"
}

variable "task_memory" {
  description = "Task memory"
  type        = string
  default     = "512"
}

