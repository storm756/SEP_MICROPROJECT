# Dynamic AMI lookup for Amazon Linux 2023 (when custom ami_id is not provided)
data "aws_ssm_parameter" "al2023" {
  count = var.ami_id == "" && !var.use_emulator ? 1 : 0
  name  = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

locals {
  ami = var.ami_id != "" ? var.ami_id : (var.use_emulator ? "ami-12345678" : data.aws_ssm_parameter.al2023[0].value)
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
    docker_image = var.docker_image
  })
  user_data_replace_on_change = true

  tags = {
    Name = "${var.name_prefix}-web-instance"
  }
}
