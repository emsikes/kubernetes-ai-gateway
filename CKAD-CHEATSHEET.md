# CKAD Cheat Sheet

Quick reference for Kubernetes commands and concepts learned while building the AI Gateway project.

---

## Cluster Management

```bash
# Start minikube with resources
minikube start --driver=docker --cpus=4 --memory=8192

# Start minikube with Calico CNI (required for NetworkPolicy enforcement)
minikube start --driver=docker --cpus=4 --memory=8192 --cni=calico

# Point Docker CLI to minikube's daemon
eval $(minikube docker-env)

# Check cluster status
minikube status
kubectl cluster-info

# Enable addons
minikube addons enable metrics-server
minikube addons enable ingress
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

# Patch to add ServiceAccount
kubectl patch deployment api-gateway -p '{"spec":{"template":{"spec":{"serviceAccountName":"api-gateway-sa"}}}}'
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

# Get minikube service URL (for Docker driver)
minikube service api-gateway -n ai-gateway --url
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

## Horizontal Pod Autoscaling (HPA)

### Enable Metrics Server (minikube)

```bash
minikube addons enable metrics-server

# Verify metrics collection (wait ~30s after enabling)
kubectl top pods
kubectl top nodes

# Sort by resource usage
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory

# Show container-level metrics
kubectl top pods --containers
```

### Create HPA (Imperative - CKAD Fast)

```bash
# Basic CPU-based HPA
kubectl autoscale deployment api-gateway --min=1 --max=5 --cpu-percent=50

# Check status
kubectl get hpa

# Watch scaling in real-time
kubectl get hpa -w

# Describe for events/conditions
kubectl describe hpa api-gateway-hpa
```

### Create HPA (Declarative - Full Control)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: ai-gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 30
      policies:
      - type: Pods
        value: 1
        periodSeconds: 15
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Pods
        value: 2
        periodSeconds: 15
```

### HPA Commands

```bash
# Quick patch threshold for testing
kubectl patch hpa api-gateway-hpa --patch '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"type":"Utilization","averageUtilization":10}}}]}}'

# Delete HPA
kubectl delete hpa api-gateway-hpa
```

### Understanding HPA Output

```
NAME              REFERENCE                TARGETS        MINPODS   MAXPODS   REPLICAS
api-gateway-hpa   Deployment/api-gateway   cpu: 251%/50%  1         5         3
```

| Field | Meaning |
|-------|---------|
| **TARGETS** | Current usage vs target (251% current / 50% target) |
| **REPLICAS** | Current pod count |
| **251%** | Pod using 2.5x its CPU *request* (not node capacity) |

**Exam Tip:** HPA scales based on resource *requests*, not limits. Pods must have requests defined.

### Load Testing for HPA

```bash
# Install hey load testing tool
sudo apt install hey

# Sustained load for 30 seconds, 10 concurrent connections
hey -z 30s -c 10 http://localhost:8080/health

# POST with JSON payload
hey -z 30s -c 10 -m POST -H "Content-Type: application/json" \
  -d '{"prompt": "test", "model": "llama3.2:1b"}' \
  http://localhost:8080/chat
```

### HPA Behavior Explained

```yaml
behavior:
  scaleUp:
    stabilizationWindowSeconds: 0    # Scale up immediately
    policies:
    - type: Pods
      value: 2                       # Add up to 2 pods
      periodSeconds: 15              # Every 15 seconds
  scaleDown:
    stabilizationWindowSeconds: 30   # Wait 30s before scaling down
    policies:
    - type: Pods
      value: 1                       # Remove 1 pod at a time
      periodSeconds: 15              # Every 15 seconds
```

**Why asymmetric?** Scale up fast to handle load spikes. Scale down slowly to prevent flapping if traffic is bursty.

---

## Ingress

### Enable Ingress Controller (minikube)

```bash
minikube addons enable ingress

# Verify controller is running
kubectl get pods -n ingress-nginx
```

### Ingress Resource

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-gateway-ingress
  namespace: ai-gateway
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: ai-gateway.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 80
```

### Ingress Commands

```bash
# List ingresses
kubectl get ingress

# Describe for details and events
kubectl describe ingress api-gateway-ingress

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=20
```

### Local Testing (minikube + Docker driver)

```bash
# Add hostname to /etc/hosts
echo "$(minikube ip) ai-gateway.local" | sudo tee -a /etc/hosts

# If tunnel needed (minikube + Docker + WSL2)
minikube tunnel

# Alternative: use minikube service directly
minikube service api-gateway -n ai-gateway --url
```

### Ingress Architecture

```
Internet → Ingress Controller (nginx pod) → Ingress Rules → Service → Pods
```

**Exam Tip:** `ingressClassName: nginx` tells Kubernetes which controller handles this Ingress. Multiple controllers can coexist.

### Path Types

| pathType | Behavior |
|----------|----------|
| `Prefix` | Matches URL path prefix (e.g., `/api` matches `/api/v1`) |
| `Exact` | Matches exact path only |
| `ImplementationSpecific` | Controller decides |

---

## NetworkPolicies

**Note:** Requires CNI that supports NetworkPolicies (Calico, Cilium). Default minikube CNI does not enforce them.

```bash
# Start minikube with Calico for NetworkPolicy support
minikube start --cni=calico
```

### Default Deny All Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: ai-gateway
spec:
  podSelector: {}      # Applies to ALL pods
  policyTypes:
  - Ingress
```

### Allow Specific Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: redis-access
  namespace: ai-gateway
spec:
  podSelector:
    matchLabels:
      app: redis           # Policy applies to redis pods
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway  # Only api-gateway can connect
    ports:
    - protocol: TCP
      port: 6379
```

### NetworkPolicy Commands

```bash
# List policies
kubectl get networkpolicy
kubectl get netpol

# Describe policy
kubectl describe networkpolicy redis-access

# Test connectivity (should fail if policy blocks it)
kubectl run test-pod --rm -it --restart=Never --image=redis:7-alpine -- redis-cli -h redis ping
```

### NetworkPolicy Mental Model

```
┌─────────────────────────────────────────────────────────────┐
│  podSelector: WHO does this policy apply to?                │
│                                                             │
│  policyTypes: WHAT traffic direction? (Ingress/Egress)      │
│                                                             │
│  ingress/egress:                                            │
│    - from/to: WHO can connect?                              │
│      - podSelector: pods with these labels                  │
│      - namespaceSelector: pods in these namespaces          │
│      - ipBlock: external IPs                                │
│    - ports: WHICH ports?                                    │
└─────────────────────────────────────────────────────────────┘
```

**Exam Tip:** Once ANY NetworkPolicy selects a pod, that pod becomes "default deny" for that traffic type. Only explicitly allowed traffic gets through.

---

## RBAC (Role-Based Access Control)

### Three Components

| Resource | Scope | Purpose |
|----------|-------|---------|
| **ServiceAccount** | Namespace | Identity for pods |
| **Role** | Namespace | Set of permissions |
| **RoleBinding** | Namespace | Connects ServiceAccount to Role |

For cluster-wide: use **ClusterRole** and **ClusterRoleBinding**

### ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-gateway-sa
  namespace: ai-gateway
```

### Role (Permissions)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-gateway-role
  namespace: ai-gateway
rules:
- apiGroups: [""]              # "" = core API
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
```

### RoleBinding (Glue)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api-gateway-binding
  namespace: ai-gateway
subjects:
- kind: ServiceAccount
  name: api-gateway-sa
  namespace: ai-gateway
roleRef:
  kind: Role
  name: api-gateway-role
  apiGroup: rbac.authorization.k8s.io
```

### Wire ServiceAccount to Pod

```yaml
spec:
  serviceAccountName: api-gateway-sa
  containers:
    - name: api-gateway
      ...
```

### RBAC Commands

```bash
# List ServiceAccounts
kubectl get serviceaccounts
kubectl get sa

# List Roles
kubectl get roles

# List RoleBindings
kubectl get rolebindings

# Check what a ServiceAccount can do
kubectl auth can-i get pods --as=system:serviceaccount:ai-gateway:api-gateway-sa

# Describe for details
kubectl describe role api-gateway-role
kubectl describe rolebinding api-gateway-binding
```

### Common Verbs

| Verb | Action |
|------|--------|
| `get` | Read single resource |
| `list` | Read collection |
| `watch` | Stream changes |
| `create` | Create new |
| `update` | Modify existing |
| `patch` | Partial modify |
| `delete` | Remove |

### RBAC Mental Model

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  ServiceAccount  │     │   RoleBinding    │     │      Role        │
│                  │◄───►│                  │◄───►│                  │
│  WHO am I?       │     │  WHO gets WHAT?  │     │  WHAT can I do?  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

**Exam Tip:** Default ServiceAccount has minimal permissions. Always create dedicated ServiceAccounts for apps that need API access.

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

# Create HPA
kubectl autoscale deployment api-gateway --min=1 --max=5 --cpu-percent=50

# Create ServiceAccount
kubectl create serviceaccount api-gateway-sa

# Create Role (then edit YAML for specific rules)
kubectl create role api-gateway-role --verb=get,list --resource=pods --dry-run=client -o yaml

# Create RoleBinding
kubectl create rolebinding api-gateway-binding --role=api-gateway-role --serviceaccount=ai-gateway:api-gateway-sa
```

---

## Quick Reference Table

| Task | Command |
|------|---------|
| Update image | `kubectl set image deployment/NAME CONTAINER=IMAGE:TAG` |
| Check rollout | `kubectl rollout status deployment/NAME` |
| Rollback | `kubectl rollout undo deployment/NAME` |
| Scale | `kubectl scale deployment/NAME --replicas=N` |
| Autoscale | `kubectl autoscale deployment/NAME --min=1 --max=5 --cpu-percent=50` |
| Port forward | `kubectl port-forward svc/NAME LOCAL:REMOTE` |
| Get logs | `kubectl logs -l app=NAME` |
| Exec into pod | `kubectl exec -it POD -- sh` |
| Env vars | `kubectl exec deployment/NAME -- env` |
| Generate YAML | `kubectl create ... --dry-run=client -o yaml` |
| Force delete | `kubectl delete pod NAME --force --grace-period=0` |
| Pod metrics | `kubectl top pods` |
| Watch HPA | `kubectl get hpa -w` |
| List ingress | `kubectl get ingress` |
| List netpol | `kubectl get networkpolicy` |
| List SA | `kubectl get serviceaccounts` |
| Check RBAC | `kubectl auth can-i VERB RESOURCE --as=system:serviceaccount:NS:SA` |

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
  serviceAccountName:    # WHO the pod runs as
  containers:            # WHAT runs (list of containers)
  volumes:               # WHAT storage (list of volumes)
  initContainers:        # WHAT runs first
  securityContext:       # HOW securely it runs
```

---

## Phase Completion Tracker

- [x] Phase 1: Pods, Deployments, Services
- [x] Phase 2: ConfigMaps, Secrets, Kustomize
- [x] Phase 3: PVCs, StatefulSets
- [x] Phase 4: Probes, Resource Limits
- [x] Phase 5: Rolling Updates, Rollbacks
- [x] Phase 6: HPA, Scaling
- [x] Phase 7: Ingress, NetworkPolicies, RBAC
- [ ] Phase 8: Provider Routing
- [ ] Phase 9: EKS Deployment
- [ ] Phase 10: ArgoCD GitOps
- [ ] Phase 11: Terraform IaC

---

*Updated: January 2026*