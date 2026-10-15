# Security Group for CityServe Web Server
resource "aws_security_group" "web" {
  name        = "${var.name_prefix}-web-sg"
  description = "Security group for CityServe civic issue web application"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.name_prefix}-web-sg"
  }
}

# Ingress Rule: Allow HTTP (Port 80)
resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.web.id
  description       = "Allow inbound HTTP traffic for web application"
  cidr_ipv4         = var.allowed_http_cidr
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

# Ingress Rule: Optional SSH (Port 22) - Only created if ssh_cidr is provided
resource "aws_vpc_security_group_ingress_rule" "ssh" {
  count             = var.ssh_cidr == "" ? 0 : 1
  security_group_id = aws_security_group.web.id
  description       = "Allow SSH management access from authorized CIDR"
  cidr_ipv4         = var.ssh_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

# Egress Rule: Full Outbound Access (for package updates and container pulls)
resource "aws_vpc_security_group_egress_rule" "all_out" {
  security_group_id = aws_security_group.web.id
  description       = "Allow all outbound traffic for container pulls and OS packages"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}
