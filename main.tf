# main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

# 1. Networking
resource "google_compute_network" "vpc_network" {
  name                    = "adk-chatbot-network"
  auto_create_subnetworks = true
}

resource "google_compute_firewall" "allow_chatbot_http" {
  name    = "allow-chatbot-http"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["8000"] # Default port for Gradio
  }

  source_ranges = ["0.0.0.0/0"] # Allow traffic from anywhere
  target_tags   = ["adk-chatbot"]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["adk-chatbot"]
}


# 2. Find the correct Debian 12 image
data "google_compute_image" "debian_image" {
  family  = "debian-12"
  project = "debian-cloud"
}

# 3. Create the Compute Instance
resource "google_compute_instance" "adk_vm" {
  name         = var.instance_name
  machine_type = var.machine_type
  tags         = ["adk-chatbot"] # Apply the tag for the firewall rule

  boot_disk {
    initialize_params {
      image = data.google_compute_image.debian_image.self_link
    }
  }

  network_interface {
    network = google_compute_network.vpc_network.id
    access_config {
      // Ephemeral public IP
    }
  }

  // This startup script automates the entire setup process
  metadata = {
    startup-script = file("startup.sh")
  }

  // Allows the instance to have full access to all Cloud APIs.
  // For better security, you should create a dedicated service account with specific roles.
  service_account {
    scopes = ["cloud-platform"]
  }
}
