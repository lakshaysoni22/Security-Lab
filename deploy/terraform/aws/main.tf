# Production Amazon Web Services (AWS) Infrastructure Provisioning
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. VPC Infrastructure Setup
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  
  tags = {
    Name = "LEAtTrace-prod-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

data "aws_availability_zones" "available" {
  state = "available"
}

# 2. RDS PostgreSQL Database Instance
resource "aws_db_instance" "postgres" {
  identifier           = "LEAtTrace-prod-db"
  allocated_storage    = 20
  db_name              = "LEAtTrace"
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t4g.micro"
  username             = "LEAtTrace_admin"
  password             = var.db_password
  parameter_group_name = "default.postgres16"
  skip_final_snapshot  = true
  
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}

resource "aws_db_subnet_group" "main" {
  name       = "LEAtTrace-db-subnets"
  subnet_ids = aws_subnet.private[*].id
}

# 3. ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "LEAtTrace-prod-redis"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis_sg.id]
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "LEAtTrace-redis-subnets"
  subnet_ids = aws_subnet.private[*].id
}

# 4. Amazon S3 Storage Bucket (Forensic Evidence Locker)
resource "aws_s3_bucket" "evidence_vault" {
  bucket        = "LEAtTrace-forensic-vault-aws-prod"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "vault_versioning" {
  bucket = aws_s3_bucket.evidence_vault.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 5. ECS Fargate Cluster & Task Definition
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "LEAtTrace-prod-cluster"
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "LEAtTrace-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "LEAtTrace-backend:latest"
    essential = true
    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
    }]
    environment = [
      { name = "DATABASE_URL", value = "postgresql://LEAtTrace_admin:${var.db_password}@${aws_db_instance.postgres.endpoint}/LEAtTrace" },
      { name = "REDIS_HOST", value = aws_elasticache_cluster.redis.cache_nodes[0].address }
    ]
  }])
}

# Security Groups
resource "aws_security_group" "db_sg" {
  name   = "LEAtTrace-db-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_security_group" "redis_sg" {
  name   = "LEAtTrace-redis-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

# Variables
variable "aws_region" {
  type    = string
  default = "ap-south-1" # Mumbai region
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Production RDS password"
  default     = "SecureAWSDBPassword2026!"
}
