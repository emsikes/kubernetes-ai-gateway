# CKAD Cheat Sheet

Quick reference for Kubernetes commands and concepts learned while building the AI Gateway project.

---

## Cluster Management

```bash
# Start minikube with resources
minikube start --driver=docker --cpus=4 --memory=8192

# Point Docker CLI to minikube's daemon
eval $(minikube docker-env)

# Check cluster status
minikube status
kubectl cluster-info
```

---

## Namespaces

```bash
# Create namespace
kubectl create namespace ai-gateway

# Set default namespace for current context
kubectl config set-context --current --namespace=ai-gateway

# List namespaces
kubectl get namespaces
```

---

## Pods

```bash
# List pods (current namespace)
kubectl get pods

# List pods (all namespaces)
kubectl get pods -A

# Watch pods in real-time
kubectl get pods -w

# Get pod details
kubectl describe pod <pod-name>

# Get pods by label
kubectl get pods -l app=api-gateway

# Delete pod by label
kubectl delete pod -l app=redis

# Run temporary pod for debugging
kubectl run test-pod --rm -it --restart=Never --image=redis:7-alpine -- sh

# Execute command in running pod
kubectl exec deployment/api-gateway -- env | grep REDIS

# View pod logs
kubectl logs <pod-name>
kubectl logs -l app=api-gateway
kubectl logs -l app=api-gateway --tail=20

# Check container image version
kubectl describe pod -l app=api-gateway | grep Image
```

---

## Deployments

```bash
# Apply deployment from file
kubectl apply -f deployment.yaml

# List deployments
kubectl get deployments

# Get deployment YAML
kubectl get deployment api-gateway -o yaml

# Update image (imperative - fast for exam)
kubectl set image deployment/api-gateway api-gateway=ai-gateway:v7

# Watch rollout status
kubectl rollout status deployment/api-gateway

# Rollback to previous version
kubectl rollout undo deployment/api-gateway

# View rollout history
kubectl rollout history deployment/api-gateway

# Scale deployment
kubectl scale deployment/api-gateway --replicas=3

# Patch deployment (e.g., fix imagePullPolicy)
kubectl patch deployment ollama -p '{"spec":{"template":{"spec":{"containers":[{"name":"ollama","imagePullPolicy":"IfNotPresent"}]}}}}'
```

---

## Services

```bash
# Apply service from file
kubectl apply -f service.yaml

# List services
kubectl get services
kubectl get svc

# Port forward to access service locally
kubectl port-forward service/api-gateway 8080:80

# Expose deployment as service (imperative)
kubectl expose deployment api-gateway --port=80 --target-port=8000
```

---

## ConfigMaps

```bash
# Create ConfigMap from file
kubectl apply -f configmap.yaml

# Create ConfigMap imperatively
kubectl create configmap my-config --from-literal=KEY=value

# Create ConfigMap from file
kubectl create configmap my-config --from-file=config.properties

# List ConfigMaps
kubectl get configmaps
kubectl get cm

# View ConfigMap contents
kubectl describe configmap api-gateway-config
kubectl get configmap api-gateway-config -o yaml
```

### ConfigMap as Environment Variables

```yaml
envFrom:
  - configMapRef:
      name: api-gateway-config
```

### ConfigMap as File Mount

```yaml
volumeMounts:
  - name: settings-volume
    mountPath: /app/config
    readOnly: true
volumes:
  - name: settings-volume
    configMap:
      name: gateway-settings
```

**Exam Tip:** Use `|` for multiline file content in ConfigMaps:
```yaml
data:
  settings.json: |
    {
      "key": "value"
    }
```

---

## Secrets

```bash
# Create Secret imperatively (preferred - keeps out of git)
kubectl create secret generic my-secret --from-literal=API_KEY=supersecret

# Create Secret from file
kubectl create secret generic my-secret --from-file=credentials.txt

# List Secrets
kubectl get secrets

# View Secret (base64 encoded)
kubectl get secret my-secret -o yaml

# Decode Secret value
kubectl get secret my-secret -o jsonpath='{.data.API_KEY}' | base64 -d
```

### Wire Secret into Deployment

```yaml
envFrom:
  - secretRef:
      name: llm-api-keys
```

---

## PersistentVolumeClaims

```bash
# Apply PVC
kubectl apply -f pvc.yaml

# List PVCs
kubectl get pvc

# Check PVC status (should be "Bound")
kubectl get pvc ollama-models
```

### PVC Definition

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-models
  namespace: ai-gateway
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Mount PVC in Deployment

```yaml
volumeMounts:
  - name: models
    mountPath: /root/.ollama
volumes:
  - name: models
    persistentVolumeClaim:
      claimName: ollama-models
```

---

## StatefulSets

**When to use StatefulSet vs Deployment:**

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod naming | Random suffix | Ordered (app-0, app-1) |
| Storage | Shared or none | Per-pod PVC |
| Startup | All at once | Sequential |
| Network | Random via Service | Stable hostname per pod |

### StatefulSet with volumeClaimTemplates

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
spec:
  serviceName: qdrant          # Required - links to headless service
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
        - name: qdrant
          image: qdrant/qdrant:latest
          volumeMounts:
            - name: qdrant-storage
              mountPath: /qdrant/storage
  volumeClaimTemplates:        # Auto-creates PVC per pod
    - metadata:
        name: qdrant-storage
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 5Gi
```

**Exam Tip:** `volumeClaimTemplates` is a sibling of `template`, both under `spec`.

### Headless Service (for StatefulSet)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: qdrant
spec:
  clusterIP: None              # Makes it headless
  selector:
    app: qdrant
  ports:
    - port: 6333
```

**Exam Tip:** `clusterIP: None` = headless. DNS returns individual pod IPs instead of a single virtual IP.

---

## Probes

### Three Probe Types

| Probe | Question | On Failure |
|-------|----------|------------|
| **Startup** | "Has it finished initializing?" | Keep waiting |
| **Liveness** | "Is it stuck/deadlocked?" | Kill and restart |
| **Readiness** | "Can it handle traffic?" | Remove from Service |

### HTTP Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 3
  periodSeconds: 5
```

### Exec Probe (for non-HTTP services like Redis)

```yaml
livenessProbe:
  exec:
    command:
      - redis-cli
      - ping
  periodSeconds: 10
```

### Startup Probe (for slow-starting apps like Ollama)

```yaml
startupProbe:
  httpGet:
    path: /api/tags
    port: 11434
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 30    # 30 x 5s = 150s max startup time
```

**Exam Tip:** Liveness and Readiness don't run until Startup succeeds.

---

## Resource Limits

```yaml
resources:
  requests:              # Minimum guaranteed
    memory: "128Mi"
    cpu: "100m"
  limits:                # Maximum allowed
    memory: "256Mi"
    cpu: "500m"
```

**Units:**
- Memory: `Mi` (mebibytes), `Gi` (gibibytes)
- CPU: `m` (millicores) - `1000m` = 1 CPU core, `100m` = 0.1 core

---

## Rolling Updates

### Strategy Configuration

```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # Extra pods during update
      maxUnavailable: 0    # Zero downtime
```

### Rollout Commands

```bash
# Watch rollout
kubectl rollout status deployment/api-gateway

# Rollback
kubectl rollout undo deployment/api-gateway

# View history
kubectl rollout history deployment/api-gateway
```

---

## Image Pull Policy

| Image Tag | Default Policy | Behavior |
|-----------|---------------|----------|
| `:latest` | `Always` | Always pulls (slow, can fail) |
| `:v1.0.0` | `IfNotPresent` | Uses cached if available |

**Exam Tip:** Always set explicitly:
```yaml
image: ollama/ollama:latest
imagePullPolicy: IfNotPresent
```

---

## Kustomize

```bash
# Preview kustomize output
kubectl kustomize manifests/base/

# Apply with kustomize
kubectl apply -k manifests/overlays/dev/
```

### Base kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
```

### Overlay with Patches

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
namePrefix: dev-
patches:
  - target:
      kind: Deployment
      name: api-gateway
    patch: |
      - op: replace
        path: /spec/replicas
        value: 1
```

---

## Debugging

```bash
# Describe resource (shows events, errors)
kubectl describe pod <pod-name>
kubectl describe deployment <deployment-name>

# Get logs
kubectl logs <pod-name>
kubectl logs -l app=api-gateway --tail=50

# Execute into pod
kubectl exec -it <pod-name> -- sh
kubectl exec -it <pod-name> -- /bin/bash

# Check environment variables
kubectl exec deployment/api-gateway -- env

# Force delete stuck pod
kubectl delete pod <pod-name> --force --grace-period=0
```

---

## Output Formatting

```bash
# Wide output (more columns)
kubectl get pods -o wide

# YAML output
kubectl get deployment api-gateway -o yaml

# JSON output
kubectl get pod <pod-name> -o json

# JSONPath (extract specific fields)
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
kubectl get secret my-secret -o jsonpath='{.data.API_KEY}' | base64 -d

# Grep through YAML
kubectl get deployment api-gateway -o yaml | grep -A 5 "strategy"
```

---

## Imperative Commands (Exam Speed)

```bash
# Generate YAML without creating (--dry-run + -o yaml)
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml

# Create deployment
kubectl create deployment nginx --image=nginx

# Create service
kubectl expose deployment nginx --port=80 --target-port=80

# Create configmap
kubectl create configmap app-config --from-literal=ENV=prod

# Create secret
kubectl create secret generic app-secret --from-literal=PASSWORD=secret

# Update image
kubectl set image deployment/api-gateway api-gateway=ai-gateway:v7
```

---

## Quick Reference Table

| Task | Command |
|------|---------|
| Update image | `kubectl set image deployment/NAME CONTAINER=IMAGE:TAG` |
| Check rollout | `kubectl rollout status deployment/NAME` |
| Rollback | `kubectl rollout undo deployment/NAME` |
| Scale | `kubectl scale deployment/NAME --replicas=N` |
| Port forward | `kubectl port-forward svc/NAME LOCAL:REMOTE` |
| Get logs | `kubectl logs -l app=NAME` |
| Exec into pod | `kubectl exec -it POD -- sh` |
| Env vars | `kubectl exec deployment/NAME -- env` |
| Generate YAML | `kubectl create ... --dry-run=client -o yaml` |
| Force delete | `kubectl delete pod NAME --force --grace-period=0` |

---

## YAML Structure Mental Models

### Volume → VolumeMount Connection

```yaml
spec:
  containers:
    - name: app
      volumeMounts:              # WHERE to mount (container level)
        - name: config-vol      # References volume by name
          mountPath: /app/config
  volumes:                       # WHAT storage is available (pod level)
    - name: config-vol          # Name referenced by volumeMount
      configMap:
        name: my-config
```

**Think of it like:** USB drive (volume) → USB port (mountPath). The `name` field is the cable connecting them.

### Pod Spec Structure

```yaml
spec:                    # Pod spec
  containers:            # WHAT runs (list of containers)
  volumes:               # WHAT storage (list of volumes)
  initContainers:        # WHAT runs first
  serviceAccountName:    # WHO the pod runs as
  securityContext:       # HOW securely it runs
```

---

## Phase Completion Tracker

- [x] Phase 1: Pods, Deployments, Services
- [x] Phase 2: ConfigMaps, Secrets, Kustomize
- [x] Phase 3: PVCs, StatefulSets
- [x] Phase 4: Probes, Resource Limits
- [ ] Phase 5: Rolling Updates, Rollbacks (in progress)
- [ ] Phase 6: HPA, Scaling
- [ ] Phase 7: Ingress, NetworkPolicies, RBAC
- [ ] Phase 8: Provider Routing
- [ ] Phase 9: EKS Deployment
- [ ] Phase 10: ArgoCD GitOps
- [ ] Phase 11: Terraform IaC

---

*Updated as project progresses*