# Production Google Cloud Platform (GCP) Infrastructure Provisioning
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.10.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. VPC Network Setup
resource "google_compute_network" "vpc" {
  name                    = "LEAtTrace-prod-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "LEAtTrace-prod-subnet"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.vpc.id
  
  private_ip_google_access = true
}

# 2. Cloud SQL Instance (PostgreSQL 16)
resource "google_sql_database_instance" "postgres" {
  name             = "LEAtTrace-prod-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = "db-f1-micro" # In development/production, scale up to db-custom-x-y
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
    backup_configuration {
      enabled    = true
      start_time = "02:00"
    }
  }
}

resource "google_sql_database" "database" {
  name     = "LEAtTrace"
  instance = google_sql_database_instance.postgres.name
}

# 3. Memorystore Redis Instance
resource "google_redis_instance" "redis" {
  name               = "LEAtTrace-prod-redis"
  tier               = "BASIC"
  memory_size_gb     = 1
  region             = var.region
  authorized_network = google_compute_network.vpc.id

  redis_version = "REDIS_7_0"
  display_name  = "LEAtTrace Cache Event Store"
}

# 4. GCS Storage Bucket (MinIO Alternative for Forensic Evidence locker)
resource "google_storage_bucket" "evidence_vault" {
  name          = "LEAtTrace-forensic-vault-${var.project_id}"
  location      = var.region
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# 5. GKE Cluster (Google Kubernetes Engine)
resource "google_container_cluster" "gke" {
  name     = "LEAtTrace-prod-cluster"
  location = var.region

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  remove_default_node_pool = true
  initial_node_count       = 1

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "primary-node-pool"
  location   = var.region
  cluster    = google_container_cluster.gke.name
  node_count = 2

  node_config {
    preemptible  = false
    machine_type = "e2-medium"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# Variables
variable "project_id" {
  type        = string
  description = "GCP Project ID to provision resources inside"
  default     = "LEAtTrace-prod"
}

variable "region" {
  type    = string
  default = "asia-south1" # Mumbai region
}
