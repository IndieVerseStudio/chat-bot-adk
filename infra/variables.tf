# variables.tf

variable "gcp_project_id" {
  type        = string
  description = "The GCP Project ID to deploy resources into."
}

variable "gcp_region" {
  type        = string
  description = "The GCP region to deploy resources into."
  default     = "asia-south1"
}

variable "gcp_zone" {
  type        = string
  description = "The GCP zone to deploy resources into."
  default     = "asia-south1-c"
}

variable "instance_name" {
  type        = string
  description = "The name of the virtual machine."
  default     = "adk-chatbot-vm"
}

variable "machine_type" {
  type        = string
  description = "The machine type for the VM."
  default     = "e2-micro"
}

variable "google_api_key" {
  type        = string
  description = "Your Google API Key for Generative AI."
  sensitive   = true # Marks this as sensitive, so it won't be shown in outputs.
}

variable "use_vertex_ai" {
  type        = bool
  description = "Set to true if using Vertex AI, false otherwise."
  default     = false
}
