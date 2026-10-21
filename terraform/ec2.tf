# Dynamic AMI lookup for Ubuntu 24.04 LTS (Noble Numbat) using EC2 DescribeImages
data "aws_ami" "ubuntu" {
  count       = var.ami_id == "" && !var.use_emulator ? 1 : 0
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

locals {
  ami = var.ami_id != "" ? var.ami_id : (var.use_emulator ? "ami-12345678" : data.aws_ami.ubuntu[0].id)
}

# EC2 Instance provisioning CityServe container
resource "aws_instance" "web" {
  ami                         = local.ami
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.web.id]
  associate_public_ip_address = true

  # Security Hardening: Enforce IMDSv2 to prevent SSRF credential theft
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  # Root EBS Volume with GP3 and encryption
  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    docker_image          = var.docker_image
    ecr_registry          = var.ecr_registry
    aws_region            = var.aws_region
    aws_access_key_id     = var.aws_access_key_id
    aws_secret_access_key = var.aws_secret_access_key
  })
  user_data_replace_on_change = true

  tags = {
    Name = "${var.name_prefix}-web-instance"
  }
}
