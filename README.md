# Kubernetes AI Gateway

![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonwebservices&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![ArgoCD](https://img.shields.io/badge/ArgoCD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)

![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)

A production-grade **Unified LLM Gateway** that routes requests to multiple AI providers based on cost, compliance, and capability requirements. Built on Kubernetes with GitOps deployment patterns.

## Project Overview

This project demonstrates enterprise patterns for LLM infrastructure:

- **Multi-provider routing** - Single API, multiple backends (Bedrock, OpenAI, Anthropic, Ollama)
- **Compliance-aware** - Route sensitive data to private inference, general queries to managed services
- **Cost optimization** - Provider selection based on token costs and rate limits
- **Cloud-native deployment** - EKS, ArgoCD, Terraform

### Architecture

```
                            ┌─────────────────────────────────────┐
                            │         API Gateway (EKS)            │
                            │  • Authentication & rate limiting    │
                            │  • Request routing logic             │
                            │  • Response caching (Redis)          │
                            │  • Cost tracking & audit logging     │
                            └────┬──────────┬──────────┬──────────┘
                                 │          │          │
        ┌────────────────────────┼──────────┼──────────┼────────────────────────┐
        │                        │          │          │                        │
        ▼                        ▼          ▼          ▼                        ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  AWS Bedrock  │    │    OpenAI     │    │   Anthropic   │    │    Ollama     │
│   (Claude)    │    │    (GPT)      │    │   (Claude)    │    │   (Local)     │
├───────────────┤    ├───────────────┤    ├───────────────┤    ├───────────────┤
│ • Managed     │    │ • Highest     │    │ • Direct API  │    │ • Private VPC │
│ • AWS-native  │    │   capability  │    │ • Alternative │    │ • PHI/HIPAA   │
│ • Pay-per-use │    │ • Enterprise  │    │   routing     │    │ • Fine-tuned  │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
```

### When to Use Each Provider

| Provider | Use Case | Why |
|----------|----------|-----|
| **AWS Bedrock** | Production workloads | Managed, scalable, AWS-native integration |
| **OpenAI** | Highest capability needs | GPT-4 for complex reasoning tasks |
| **Anthropic** | Direct API fallback | Alternative routing, cost comparison |
| **Ollama** | Sensitive data / compliance | PHI, HIPAA, air-gapped, fine-tuned models |

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | Kubernetes (EKS) | Container orchestration |
| **GitOps** | ArgoCD | Declarative deployments |
| **Infrastructure** | Terraform | IaC for reproducible environments |
| **API Gateway** | FastAPI | Request routing, auth, caching |
| **Cache** | Redis | Response caching, rate limiting |
| **Local Inference** | Ollama | Private LLM for sensitive data |
| **Vector Store** | Qdrant | Embedding storage (RAG support) |
| **CI/CD** | GitHub Actions | Build and push images |

## Project Phases

| Phase | Focus | Status | Key Learnings |
|-------|-------|--------|---------------|
| 1 | K8s Foundation | ✅ Complete | Pods, Deployments, Services, Labels |
| 2 | Configuration | ✅ Complete | ConfigMaps, Secrets, Kustomize |
| 3 | Persistence | ✅ Complete | PVCs, StatefulSets |
| 4 | Observability | ✅ Complete | Probes, Resource Limits |
| 5 | Deployment Strategies | 🔄 In Progress | Rolling Updates, Rollbacks, Canary |
| 6 | Scaling | ⬜ Planned | HPA, Load Testing |
| 7 | Ingress & Security | ⬜ Planned | Ingress, NetworkPolicies, RBAC |
| 8 | Provider Routing | ⬜ Planned | Bedrock, OpenAI, Anthropic integration |
| 9 | EKS Deployment | ⬜ Planned | Production cloud deployment |
| 10 | ArgoCD GitOps | ⬜ Planned | Declarative application delivery |
| 11 | Terraform IaC | ⬜ Planned | Infrastructure as Code |

## Local Development

### Prerequisites

- Docker
- minikube
- kubectl
- AWS CLI (for Bedrock integration)

### Quick Start

```bash
# Start minikube
minikube start --driver=docker --cpus=4 --memory=8192

# Create namespace
kubectl create namespace ai-gateway
kubectl config set-context --current --namespace=ai-gateway

# Point Docker to minikube
eval $(minikube docker-env)

# Build API Gateway
cd api-gateway
docker build -t ai-gateway:v1 .

# Deploy all services
cd ../manifests/base
kubectl apply -k .

# Configure secrets (optional - for external providers)
kubectl create secret generic llm-api-keys \
  --from-literal=OPENAI_API_KEY=your-key \
  --from-literal=ANTHROPIC_API_KEY=your-key

# Test
kubectl port-forward service/api-gateway 8080:80
curl http://localhost:8080/health
curl http://localhost:8080/providers
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check for K8s probes |
| `/config` | GET | Display current configuration |
| `/providers` | GET | List configured LLM providers |
| `/settings` | GET | Show routing settings |
| `/chat` | POST | Send inference request |
| `/redis-test` | GET | Verify cache connectivity |

### Example Chat Request

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Kubernetes in one sentence",
    "model": "llama3.2:1b"
  }'
```

## Project Structure

```
kubernetes-ai-gateway/
├── api-gateway/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── manifests/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── api-gateway-deployment.yaml
│   │   ├── api-gateway-service.yaml
│   │   ├── api-gateway-config.yaml
│   │   ├── gateway-settings.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── redis-service.yaml
│   │   ├── ollama-deployment.yaml
│   │   ├── ollama-service.yaml
│   │   ├── ollama-pvc.yaml
│   │   ├── qdrant-statefulset.yaml
│   │   └── qdrant-service.yaml
│   └── overlays/
│       ├── dev/
│       └── prod/
├── terraform/           # Coming Phase 11
├── argocd/              # Coming Phase 10
├── CKAD-CHEATSHEET.md
└── README.md
```

## Key Design Decisions

### Why a Gateway Instead of Direct Provider Calls?

| Concern | Gateway Solution |
|---------|------------------|
| **Vendor lock-in** | Swap providers without code changes |
| **Cost control** | Centralized tracking and routing |
| **Compliance** | Route PHI to private inference |
| **Reliability** | Fallback providers, caching |
| **Observability** | Unified logging and metrics |

### Why Self-Hosted Ollama?

Not a replacement for Bedrock - a complement for specific cases:

- **Healthcare/PHI**: Data never leaves your VPC
- **Fine-tuned models**: Custom models not available in managed services
- **Air-gapped environments**: No external API access
- **Development**: Fast iteration without API costs

## CKAD Exam Alignment

This project covers these CKAD domains:

| Domain | Concepts Practiced |
|--------|-------------------|
| Application Design & Build | Multi-container pods, init containers |
| Application Deployment | Rolling updates, rollbacks, scaling |
| Application Observability | Probes, logging, resource monitoring |
| Application Environment | ConfigMaps, Secrets, env vars |
| Services & Networking | Services, Ingress, NetworkPolicies |

See [CKAD-CHEATSHEET.md](./CKAD-CHEATSHEET.md) for exam tips learned during this project.

## Roadmap

- [x] Core K8s deployment (minikube)
- [x] ConfigMaps and Secrets management
- [x] Persistent storage (PVCs, StatefulSets)
- [x] Health probes and resource limits
- [ ] Deployment strategies (rolling, canary)
- [ ] Horizontal Pod Autoscaler
- [ ] Ingress with TLS
- [ ] NetworkPolicies
- [ ] AWS Bedrock integration
- [ ] OpenAI/Anthropic routing
- [ ] EKS deployment
- [ ] ArgoCD GitOps
- [ ] Terraform automation

## Author

**Matt Sikes** - Principal Architect specializing in AI infrastructure and cloud solutions

## License

MIT