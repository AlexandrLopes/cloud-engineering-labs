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

  # Deliberately no `ports` block — Postgres is reachable only from other
  # containers on platform-network, never from the host or outside it.
  restart = "unless-stopped"
}

resource "docker_container" "node_exporter" {
  name  = "node-exporter"
  image = docker_image.node_exporter.image_id

  networks_advanced {
    name = docker_network.platform_network.name
  }

  # No external port — Node Exporter is scraped by Prometheus over the
  # internal network, not meant to be reachable from the host directly.
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

  # No external port — Prometheus is reached through Nginx (/prometheus/),
  # not directly. This is the fix: previously `external = 9090` here made
  # the "single entry point" claim in the README false.
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

  env = [
    # Grafana is served under the /grafana/ subpath via Nginx — it needs to
    # know that, or its own internal links break.
    "GF_SERVER_ROOT_URL=http://localhost/grafana/",
    "GF_SERVER_SERVE_FROM_SUB_PATH=true"
  ]

  # No external port — reached through Nginx (/grafana/), not directly.
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
