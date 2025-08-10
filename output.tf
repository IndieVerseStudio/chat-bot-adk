# outputs.tf

output "vm_public_ip" {
  description = "The public IP address of the VM."
  value       = google_compute_instance.adk_vm.network_interface[0].access_config[0].nat_ip
}

output "chatbot_url" {
  description = "URL to access the chatbot application."
  value       = "http://${google_compute_instance.adk_vm.network_interface[0].access_config[0].nat_ip}:8000"
}
