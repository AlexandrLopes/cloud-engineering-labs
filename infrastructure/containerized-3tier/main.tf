terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "platform_network" {
  name = "platform-network"
}

resource "docker_volume" "postgres_data" {
  name = "postgres-data"
}

resource "docker_volume" "grafana_data" {
  name = "grafana-data"
}

resource "docker_image" "postgres" {
  name         = "postgres:15"
  keep_locally = true
}

resource "docker_image" "prometheus" {
  name         = "prom/prometheus:latest"
  keep_locally = true
}

resource "docker_image" "grafana" {
  name         = "grafana/grafana:latest"
  keep_locally = true
}

resource "docker_image" "node_exporter" {
  name         = "prom/node-exporter:latest"
  keep_locally = true
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "postgres" {
  name  = "postgres"
  image = docker_image.postgres.image_id

  env = [
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
    "POSTGRES_DB=${var.postgres_db}"
  ]

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  networks_advanced {
    name = docker_network.platform_network.name
  }

  restart = "unless-stopped"
}

resource "docker_container" "node_exporter" {
  name  = "node-exporter"
  image = docker_image.node_exporter.image_id

  networks_advanced {
    name = docker_network.platform_network.name
  }

  ports {
    internal = 9100
    external = 9100
  }

  restart = "unless-stopped"
}

resource "docker_container" "prometheus" {
  name  = "prometheus"
  image = docker_image.prometheus.image_id

  volumes {
    host_path      = abspath("${path.module}/prometheus/prometheus.yml")
    container_path = "/etc/prometheus/prometheus.yml"
  }

  networks_advanced {
    name = docker_network.platform_network.name
  }

  ports {
    internal = 9090
    external = 9090
  }

  restart = "unless-stopped"
}

resource "docker_container" "grafana" {
  name  = "grafana"
  image = docker_image.grafana.image_id

  volumes {
    volume_name    = docker_volume.grafana_data.name
    container_path = "/var/lib/grafana"
  }

  networks_advanced {
    name = docker_network.platform_network.name
  }

  ports {
    internal = 3000
    external = 3000
  }

  restart = "unless-stopped"
}

resource "docker_container" "nginx" {
  name  = "nginx"
  image = docker_image.nginx.image_id

  volumes {
    host_path      = abspath("${path.module}/nginx/nginx.conf")
    container_path = "/etc/nginx/nginx.conf"
  }

  networks_advanced {
    name = docker_network.platform_network.name
  }

  ports {
    internal = 80
    external = 80
  }

  restart = "unless-stopped"
}