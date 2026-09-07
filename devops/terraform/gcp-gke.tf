# Google Cloud Platform Infrastructure Provisioner

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

variable "gcp_project_id" {
  type    = string
  default = "LEAtTrace-prod-gcp"
}

variable "gcp_region" {
  type    = string
  default = "asia-south1" # Mumbai region
}

# 1. VPC Network
resource "google_compute_network" "vpc" {
  name                    = "LEAtTrace-gcp-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "LEAtTrace-gcp-subnet"
  ip_cidr_range = "10.1.0.0/24"
  region        = var.gcp_region
  network       = google_compute_network.vpc.id
}

# 2. Google Kubernetes Engine (GKE) Cluster
resource "google_container_cluster" "gke" {
  name                     = "LEAtTrace-gke-cluster"
  location                 = var.gcp_region
  remove_default_node_pool = true
  initial_node_count       = 1
  network                  = google_compute_network.vpc.name
  subnetwork               = google_compute_subnetwork.subnet.name
}

resource "google_container_node_pool" "gke_nodes" {
  name       = "LEAtTrace-node-pool"
  location   = var.gcp_region
  cluster    = google_container_cluster.gke.name
  node_count = 3

  node_config {
    preemptible  = false
    machine_type = "e2-standard-4"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

# 3. Google Cloud SQL (PostgreSQL)
resource "google_sql_database_instance" "postgres" {
  name             = "LEAtTrace-cloud-sql"
  database_version = "POSTGRES_15"
  region           = var.gcp_region
  settings {
    tier = "db-custom-2-7680"
  }
}

# 4. Google Cloud Memorystore (Redis)
resource "google_redis_instance" "redis" {
  name           = "LEAtTrace-redis"
  tier           = "STANDARD_HA"
  memory_size_gb = 5
  region         = var.gcp_region
}

# 5. Cloud Storage Bucket (Evidence Vault)
resource "google_storage_bucket" "vault" {
  name          = "LEAtTrace-gcp-vault-storage"
  location      = var.gcp_region
  force_destroy = true
}
