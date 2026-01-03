# Kubernetes AI Gateway

![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-D4A27F?style=for-the-badge&logo=anthropic&logoColor=white)

![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![CKAD](https://img.shields.io/badge/CKAD-Exam%20Prep-blue)

A production-style AI/LLM inference platform built on Kubernetes, designed as a hands-on learning project for CKAD (Certified Kubernetes Application Developer) exam preparation.

## Project Overview

This project deploys a multi-service AI inference platform that exercises core Kubernetes concepts through real-world patterns. Rather than abstract examples, each component serves a practical purpose in an LLM gateway architecture.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Ingress                               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              API Gateway (FastAPI)                           │
│         - Auth, routing, rate limiting                       │
└──────┬──────────────────┬────────────────────┬──────────────┘
       │                  │                    │
┌──────▼──────┐   ┌───────▼───────┐   ┌───────▼───────┐
│ LLM Service │   │ Embedding Svc │   │  Redis Cache  │
│  (Ollama)   │   │  (FastAPI)    │   │               │
└─────────────┘   └───────┬───────┘   └───────────────┘
                          │
                  ┌───────▼───────┐
                  │ Vector Store  │
                  │  (Qdrant)     │
                  └───────────────┘
```

### LLM Provider Support

The gateway supports multiple inference backends:

| Provider | Type | Authentication | Use Case |
|----------|------|----------------|----------|
| Ollama | Local (in-cluster) | None required | Free inference, no external dependencies |
| OpenAI | External API | API Key via K8s Secret | GPT models, production workloads |
| Anthropic | External API | API Key via K8s Secret | Claude models, production workloads |

Provider credentials are managed via Kubernetes Secrets, following security best practices for sensitive configuration.

## CKAD Concepts Covered

| Phase | Focus Area | K8s Concepts | Status |
|-------|------------|--------------|--------|
| 1 | Foundation | Pods, Deployments, Services, Labels, Selectors | ✅ Complete |
| 2 | Configuration | ConfigMaps, Secrets, Environment Variables | ✅ Complete |
| 3 | Persistence | PersistentVolumeClaims, StatefulSets, StorageClasses | ✅ Complete |
| 4 | Observability | Probes (Liveness/Readiness/Startup), Resource Limits, Logging | ⬜ Planned |
| 5 | Deployment Strategies | Rolling Updates, Rollbacks, Blue-Green, Canary | ⬜ Planned |
| 6 | Scaling | HorizontalPodAutoscaler, Manual Scaling, Load Testing | ⬜ Planned |
| 7 | Networking & Security | Ingress, NetworkPolicies, SecurityContext, RBAC | ⬜ Planned |

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Container Orchestration | Kubernetes (minikube) | Local K8s cluster |
| API Gateway | FastAPI + Uvicorn | Request routing, health checks |
| Cache | Redis | Session/response caching |
| LLM Inference | Ollama | Local model serving |
| External LLMs | OpenAI, Anthropic | Cloud-based inference |
| Vector Store | Qdrant | Embedding storage (planned) |
| Container Runtime | Docker | Image building |

## Project Structure

```
kubernetes-ai-gateway/
├── api-gateway/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── manifests/
│   ├── redis-deployment.yaml
│   ├── redis-service.yaml
│   ├── api-gateway-deployment.yaml
│   ├── api-gateway-service.yaml
│   └── api-gateway-config.yaml
├── CKAD-CHEATSHEET.md
├── .gitignore
└── README.md
```

## Quick Start

### Prerequisites

- Docker
- minikube
- kubectl

### Setup

1. **Start minikube cluster**
   ```bash
   minikube start --driver=docker --cpus=4 --memory=8192
   ```

2. **Create namespace**
   ```bash
   kubectl create namespace ai-gateway
   kubectl config set-context --current --namespace=ai-gateway
   ```

3. **Point Docker to minikube**
   ```bash
   eval $(minikube docker-env)
   ```

4. **Build the API Gateway image**
   ```bash
   cd api-gateway
   docker build -t ai-gateway:v1 .
   ```

5. **Deploy all services**
   ```bash
   cd ../manifests
   kubectl apply -f redis-deployment.yaml
   kubectl apply -f redis-service.yaml
   kubectl apply -f api-gateway-config.yaml
   kubectl apply -f api-gateway-deployment.yaml
   kubectl apply -f api-gateway-service.yaml
   ```

6. **Configure LLM Provider Secrets (optional)**
   ```bash
   kubectl create secret generic llm-api-keys \
     --from-literal=OPENAI_API_KEY=your-openai-key \
     --from-literal=ANTHROPIC_API_KEY=your-anthropic-key
   ```

7. **Verify deployment**
   ```bash
   kubectl get pods
   kubectl get services
   ```

8. **Test the API**
   ```bash
   kubectl port-forward service/api-gateway 8080:80
   # In another terminal:
   curl http://localhost:8080/health
   curl http://localhost:8080/redis-test
   curl http://localhost:8080/config
   curl http://localhost:8080/providers
   ```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check for K8s probes |
| `/redis-test` | GET | Verify Redis connectivity |
| `/config` | GET | Display current configuration |
| `/providers` | GET | List configured LLM providers |

## Key Learnings

### Service Discovery
Kubernetes DNS automatically resolves service names to pod IPs. The API Gateway connects to Redis simply using the hostname `redis`, which K8s resolves to the Redis service's ClusterIP.

### Environment Variable Injection
Configuration is injected via the Deployment manifest rather than baked into images, enabling the same image to run in different environments.

### ConfigMaps vs Secrets
- **ConfigMaps**: Non-sensitive configuration (app settings, feature flags)
- **Secrets**: Sensitive data (API keys, credentials) - base64 encoded and can be encrypted at rest

### Labels and Selectors
Deployments manage pods through label matching. Services route traffic using the same mechanism, creating a decoupled architecture.

### Rolling Updates
Changing the image tag in a Deployment triggers a rolling update. Kubernetes gradually replaces old pods with new ones, maintaining availability throughout.

## Roadmap

- [x] Add ConfigMaps for externalized configuration
- [x] Implement Secrets for API key management
- [ ] Deploy Ollama with PersistentVolumeClaim for model storage
- [ ] Add health probes (liveness, readiness, startup)
- [ ] Configure resource requests and limits
- [ ] Implement HorizontalPodAutoscaler
- [ ] Add Ingress for external access
- [ ] Implement NetworkPolicies for pod isolation
- [ ] Build LLM routing logic (Ollama/OpenAI/Anthropic)
- [ ] Add response caching with Redis

## Author

Matt Sikes - Principal Architect specializing in AI infrastructure and cloud solutions

## License

MIT
