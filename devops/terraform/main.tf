provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "ap-south-1" # Mumbai region for cyber crime forensics compliance
}

variable "environment" {
  default = "production"
}

# 1. VPC Configuration
resource "aws_vpc" "LEAtTrace_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name        = "LEAtTrace-vpc-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.LEAtTrace_vpc.id
}

resource "aws_subnet" "public_subnet_a" {
  vpc_id            = aws_vpc.LEAtTrace_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "ap-south-1a"
}

resource "aws_subnet" "private_subnet_a" {
  vpc_id            = aws_vpc.LEAtTrace_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "ap-south-1a"
}

# 2. IAM Roles for EKS
resource "aws_iam_role" "eks_cluster_role" {
  name = "LEAtTrace-eks-cluster-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

# 3. Amazon EKS Cluster
resource "aws_eks_cluster" "eks" {
  name     = "LEAtTrace-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = [
      aws_subnet.public_subnet_a.id,
      aws_subnet.private_subnet_a.id
    ]
  }
  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
}

# 4. Amazon RDS PostgreSQL
resource "aws_db_instance" "rds_postgres" {
  allocated_storage      = 100
  max_allocated_storage  = 500
  engine                 = "postgres"
  engine_version         = "15.3"
  instance_class         = "db.r6g.large"
  db_name                = "LEAtTrace"
  username               = "LEAtTrace_admin"
  password               = "SecureDbPass2026"
  parameter_group_name   = "default.postgres15"
  skip_final_snapshot    = true
  multi_az               = true
  storage_encrypted      = true
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.db_sg.id]
}

# 5. Amazon ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id        = "LEAtTrace-redis-group"
  description                 = "LEAtTrace High Availability Cache Store"
  node_type                   = "cache.t4g.medium"
  num_cache_clusters          = 2
  parameter_group_name        = "default.redis7"
  port                        = 6379
  multi_az_enabled            = true
  automatic_failover_enabled  = true
  transit_encryption_enabled = true
  auth_token                  = "SecureRedisAuthToken2026"
  security_group_ids          = [aws_security_group.redis_sg.id]
}

# 6. S3 Bucket for Evidence/Audit Log Storage
resource "aws_s3_bucket" "evidence_store" {
  bucket = "LEAtTrace-evidence-vault-prod"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_encrypt" {
  bucket = aws_s3_bucket.evidence_store.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Security Groups
resource "aws_security_group" "db_sg" {
  name        = "LEAtTrace-db-sg"
  description = "Allows backend connection to database"
  vpc_id      = aws_vpc.LEAtTrace_vpc.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_security_group" "redis_sg" {
  name        = "LEAtTrace-redis-sg"
  description = "Allows backend connection to Redis cluster"
  vpc_id      = aws_vpc.LEAtTrace_vpc.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}
