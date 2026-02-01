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
- **OpenAI-compatible API** - Drop-in replacement for any OpenAI client
- **Compliance-aware** - Route sensitive data to private inference, general queries to managed services
- **Cost optimization** - Provider selection based on token costs and rate limits
- **Content safety guardrails** - Config-driven moderation with PII protection
- **Cloud-native deployment** - EKS, ArgoCD, Terraform

### Architecture

```
                            ┌─────────────────────────────────────┐
                            │         API Gateway (EKS)            │
                            │  • Authentication & rate limiting    │
                            │  • Content safety guardrails         │
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
| **OpenAI** | Highest capability needs | GPT-5.x for complex reasoning tasks |
| **Anthropic** | Direct API fallback | Alternative routing, cost comparison |
| **Ollama** | Sensitive data / compliance | PHI, HIPAA, air-gapped, fine-tuned models |

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | Kubernetes (EKS) | Container orchestration |
| **GitOps** | ArgoCD | Declarative deployments |
| **Infrastructure** | Terraform | IaC for reproducible environments |
| **API Gateway** | FastAPI | Request routing, auth, caching |
| **Cache** | Redis | Response caching, rate limiting, usage metrics |
| **Local Inference** | Ollama | Private LLM for sensitive data |
| **Vector Store** | Qdrant | Embedding storage (RAG support) |
| **CI/CD** | GitHub Actions | Build and push images |

## Project Phases

| Phase | Focus | Status | Key Learnings |
|-------|-------|--------|---------------|
| 1 | K8s Foundation | ✅ Complete | Pods, Deployments, Services, Labels |
| 2 | Configuration | ✅ Complete | ConfigMaps, Secrets, Kustomize |
| 3 | Persistence | ✅ Complete | PVCs, StatefulSets, Headless Services |
| 4 | Observability | ✅ Complete | Probes (startup/liveness/readiness), Resource Limits |
| 5 | Deployment Strategies | ✅ Complete | Rolling Updates, Rollbacks, Blue-Green |
| 6 | Scaling | ✅ Complete | HPA, Metrics Server, Load Testing |
| 7 | Ingress & Security | ✅ Complete | Ingress, NetworkPolicies, RBAC |
| 8 | Provider Routing | 🔄 In Progress | Modular provider architecture, config-driven routing |
| 9 | Router Enhancements | ⬜ Planned | Private routing, cost-based selection, fallback logic |
| 10 | Guardrails Phase 1 | ⬜ Planned | Content safety, prompt injection detection |
| 11 | Guardrails Phase 2 | ⬜ Planned | PII detection & masking, jailbreak protection |
| 12 | EKS Deployment | ⬜ Planned | Production cloud deployment with Route53 |
| 13 | ArgoCD GitOps | ⬜ Planned | Declarative application delivery |
| 14 | Terraform IaC | ⬜ Planned | Infrastructure as Code |

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

### Enable Addons (for full functionality)

```bash
# Metrics for HPA
minikube addons enable metrics-server

# Ingress controller
minikube addons enable ingress

# Verify
kubectl top pods
kubectl get pods -n ingress-nginx
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check for K8s probes |
| `/config` | GET | Display current configuration |
| `/providers` | GET | List configured LLM providers |
| `/settings` | GET | Show routing settings |
| `/v1/chat/completions` | POST | OpenAI-compatible chat endpoint |
| `/redis-test` | GET | Verify cache connectivity |

### Example Chat Request (OpenAI-compatible)

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {"role": "user", "content": "Explain Kubernetes in one sentence"}
    ]
  }'
```

**Response:**
```json
{
  "id": "ollama-3c2f64f8",
  "object": "chat.completion",
  "created": 1737590400,
  "model": "llama3.2:1b",
  "provider": "ollama",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Kubernetes is an open-source container orchestration platform..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 35,
    "completion_tokens": 10,
    "total_tokens": 45
  }
}
```

## Project Structure

```
kubernetes-ai-gateway/
├── api-gateway/
│   ├── main.py              # FastAPI app, routes, provider initialization
│   ├── models.py            # Pydantic models (ChatRequest, ChatResponse)
│   ├── providers/
│   │   ├── __init__.py      # Provider exports
│   │   ├── base.py          # LLMProvider abstract base class
│   │   ├── ollama.py        # Ollama provider implementation
│   │   └── openai.py        # OpenAI provider implementation
│   ├── guardrails/          # Content moderation (Phase 10-11)
│   │   ├── __init__.py      # Guardrail exports
│   │   ├── base.py          # GuardrailBase abstract class
│   │   ├── content_safety.py # Phase 1: Content safety evaluation
│   │   └── pii_guard.py     # Phase 2: PII detection & masking
│   ├── requirements.txt
│   └── Dockerfile
├── manifests/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── api-gateway-deployment.yaml
│   │   ├── api-gateway-service.yaml
│   │   ├── api-gateway-config.yaml
│   │   ├── api-gateway-hpa.yaml
│   │   ├── api-gateway-ingress.yaml
│   │   ├── api-gateway-rbac.yaml
│   │   ├── gateway-settings.yaml    # Provider model routing config
│   │   ├── guardrail-settings.yaml  # Content safety config (Phase 10)
│   │   ├── redis-deployment.yaml
│   │   ├── redis-service.yaml
│   │   ├── redis-network-policy.yaml
│   │   ├── ollama-deployment.yaml
│   │   ├── ollama-service.yaml
│   │   ├── ollama-pvc.yaml
│   │   ├── qdrant-statefulset.yaml
│   │   └── qdrant-service.yaml
│   └── overlays/
│       ├── dev/
│       └── prod/
├── terraform/           # Coming Phase 14
├── argocd/              # Coming Phase 13
├── CKAD-CHEATSHEET.md
└── README.md
```

## Provider Routing

Model-to-provider mapping is configured via ConfigMap (`gateway-settings.yaml`):

```json
{
  "provider_models": {
    "openai": ["gpt-5", "gpt-4", "gpt-3.5", "o1", "o3"],
    "anthropic": ["claude"],
    "bedrock": ["amazon", "anthropic.claude", "meta.llama"],
    "ollama": ["llama", "mistral", "codellama", "phi", "qwen"]
  }
}
```

The router automatically selects a provider based on the model name prefix. Update the ConfigMap to add new models without code changes.

## Guardrails Architecture

Config-driven content moderation that intercepts requests before they reach LLM providers. Categories and rules are managed via ConfigMap - no code rebuild required for updates.

### Phase 1: Content Safety

| Category | What It Detects |
|----------|-----------------|
| `SELF_HARM` | Suicide, self-injury, eating disorders |
| `VIOLENCE` | Threats, harm to others, graphic violence |
| `HATE_SPEECH` | Discrimination, slurs, targeted harassment |
| `SEXUAL_CONTENT` | Explicit sexual content, pornography |
| `ILLEGAL_ACTIVITY` | Fraud, scams, theft |
| `CONTROLLED_SUBSTANCES` | Drugs, drug manufacturing |
| `WEAPONS` | Weapon manufacturing, illegal weapons |
| `CYBER_CRIME` | Hacking, malware, exploits, phishing |
| `CHILD_SAFETY` | CSAM references, grooming, exploitation |
| `TERRORISM` | Extremist content, radicalization |
| `PROMPT_INJECTION` | "Ignore instructions", role hijacking |
| `OFFENSIVE_LANGUAGE` | Profanity, explicit language |

### Phase 2: Advanced Protection

| Feature | Description |
|---------|-------------|
| PII Detection | SSN, email, phone, credit cards, names, addresses |
| PII Masking | Redact or mask before sending to external LLMs |
| Jailbreak Detection | DAN prompts, persona manipulation, encoding tricks |

### Configuration

Guardrails are configured via `guardrail-settings.yaml` ConfigMap:

```yaml
categories:
  SELF_HARM:
    enabled: true
    severity: critical
    action: block
    keywords: ["suicide", "kill myself", "end my life"]
  VIOLENCE:
    enabled: true
    severity: high
    action: block
```

Update categories without code changes:

```bash
kubectl edit configmap guardrail-settings
kubectl rollout restart deployment/api-gateway
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

### Why Config-Driven Guardrails?

- **No rebuild required** - Update keywords and rules via ConfigMap
- **Environment-specific** - Different rules for dev vs prod
- **Audit-friendly** - Configuration changes tracked in Git
- **Rapid response** - Block new threats without deployment

## Security Features

### RBAC (Role-Based Access Control)

API Gateway runs with a dedicated ServiceAccount with least-privilege permissions:

```yaml
# api-gateway-sa can only:
- get/list ConfigMaps and Secrets (in ai-gateway namespace)
- get/list/watch Pods (for health monitoring)
```

### NetworkPolicies

Redis access restricted to api-gateway pods only:

```yaml
# Only pods with label app=api-gateway can reach Redis on port 6379
```

**Note:** NetworkPolicy enforcement requires Calico CNI. Will be fully tested on EKS deployment.

### Content Safety (Phase 10-11)

- Pre-LLM request scanning for harmful content
- PII detection and masking before external API calls
- Prompt injection and jailbreak detection
- Configurable block/warn/log actions per category

## CKAD Exam Alignment

This project covers these CKAD domains:

| Domain | Concepts Practiced |
|--------|-------------------|
| Application Design & Build | Multi-container pods, init containers |
| Application Deployment | Rolling updates, rollbacks, HPA scaling |
| Application Observability | Probes, logging, resource monitoring |
| Application Environment | ConfigMaps, Secrets, env vars |
| Services & Networking | Services, Ingress, NetworkPolicies |

See [CKAD-CHEATSHEET.md](./CKAD-CHEATSHEET.md) for exam tips learned during this project.

## Roadmap

- [x] Core K8s deployment (minikube)
- [x] ConfigMaps and Secrets management
- [x] Persistent storage (PVCs, StatefulSets)
- [x] Health probes and resource limits
- [x] Deployment strategies (rolling, blue-green)
- [x] Horizontal Pod Autoscaler
- [x] Ingress with nginx controller
- [x] NetworkPolicies (Redis isolation)
- [x] RBAC (ServiceAccount, Role, RoleBinding)
- [x] Modular provider architecture
- [x] Config-driven model routing
- [x] Ollama provider with OpenAI-compatible API
- [x] Redis usage metrics per provider
- [ ] OpenAI provider (built, needs testing)
- [ ] Anthropic provider
- [ ] AWS Bedrock provider
- [ ] Router enhancements (private flag, max_cost, fallback)
- [ ] Guardrails Phase 1: Content safety guard
- [ ] Guardrails Phase 2: PII detection & masking
- [ ] EKS deployment with Route53 DNS
- [ ] ArgoCD GitOps
- [ ] Terraform automation

## Author

**Matt Sikes** - Principal Architect specializing in AI infrastructure and cloud solutions

## License

MIT