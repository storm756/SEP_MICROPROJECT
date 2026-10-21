variable "aws_region" {
  description = "AWS Region to deploy infrastructure"
  type        = string
  default     = "ap-south-1" # Mumbai region
}

variable "instance_type" {
  description = "EC2 instance type (Free Tier eligible)"
  type        = string
  default     = "t3.micro"
}

variable "name_prefix" {
  description = "Prefix for resource naming"
  type        = string
  default     = "cityserve"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.20.1.0/24"
}

variable "allowed_http_cidr" {
  description = "CIDR block allowed to access HTTP (Port 80)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "ssh_cidr" {
  description = "CIDR block allowed for SSH access (Port 22) - empty disables SSH"
  type        = string
  default     = ""
}

variable "docker_image" {
  description = "Docker image repository and tag to deploy"
  type        = string
  default     = "318724431625.dkr.ecr.ap-south-1.amazonaws.com/cityserve:latest"
}

variable "ecr_registry" {
  description = "AWS ECR registry domain"
  type        = string
  default     = "318724431625.dkr.ecr.ap-south-1.amazonaws.com"
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID for ECR authentication"
  type        = string
  default     = ""
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key for ECR authentication"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ami_id" {
  description = "Custom AMI ID (optional, defaults to latest Amazon Linux 2023)"
  type        = string
  default     = ""
}

variable "use_emulator" {
  description = "Set to true when running against a local AWS emulator (Floci/LocalStack)"
  type        = bool
  default     = false
}

variable "emulator_endpoint" {
  description = "Local emulator endpoint URL"
  type        = string
  default     = "http://localhost:4566"
}
