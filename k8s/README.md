# Kubernetes Deployment

Este directorio contiene los manifiestos de Kubernetes para desplegar la API en producción.

## Archivos

- `00-secret.yaml`: Secret con las API keys (ANTHROPIC_API_KEY, MASTER_API_KEY)
- `01-deployment.yaml`: Deployment con 2 réplicas de la API
- `02-service.yaml`: Service ClusterIP para exponer el deployment
- `03-ingress.yaml`: Ingress con Traefik para exponer en tfm-ai-api.helmcode.com

## Despliegue

### 1. Configurar secrets

Edita `00-secret.yaml` y reemplaza los valores `CHANGE_ME` con tus claves reales:

```bash
# Editar manualmente o usar kubectl create secret
kubectl create secret generic tfm-ai-api-secrets \
  --from-literal=ANTHROPIC_API_KEY=tu_clave_anthropic \
  --from-literal=MASTER_API_KEY=tu_clave_maestra \
  -n tfm-ai-api
```

### 2. Aplicar manifiestos

```bash
# Aplicar todos los manifiestos
kubectl --kubeconfig=~/.kube/helmcode/prod apply -f k8s/

# O aplicar uno por uno
kubectl --kubeconfig=~/.kube/helmcode/prod apply -f k8s/00-secret.yaml
kubectl --kubeconfig=~/.kube/helmcode/prod apply -f k8s/01-deployment.yaml
kubectl --kubeconfig=~/.kube/helmcode/prod apply -f k8s/02-service.yaml
kubectl --kubeconfig=~/.kube/helmcode/prod apply -f k8s/03-ingress.yaml
```

### 3. Verificar despliegue

```bash
# Ver pods
kubectl --kubeconfig=~/.kube/helmcode/prod get pods -n tfm-ai-api

# Ver logs
kubectl --kubeconfig=~/.kube/helmcode/prod logs -f deployment/tfm-ai-api -n tfm-ai-api

# Ver ingress
kubectl --kubeconfig=~/.kube/helmcode/prod get ingress -n tfm-ai-api

# Verificar servicio
kubectl --kubeconfig=~/.kube/helmcode/prod get svc -n tfm-ai-api
```

### 4. Probar API

```bash
# Health check
curl https://tfm-ai-api.helmcode.com/health

# Test endpoint
curl -X POST https://tfm-ai-api.helmcode.com/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tu_master_api_key" \
  -d '{"message": "¿Cuántos turistas visitaron Tenerife?"}'
```

## Recursos

- **Replicas**: 2 pods para alta disponibilidad
- **CPU**: 250m request, 500m limit
- **Memory**: 512Mi request, 1Gi limit
- **Health checks**: Liveness y Readiness probes en `/health`
- **TLS**: Certificado automático con cert-manager (letsencrypt-prod)

## Notas

- El deployment clona el repositorio desde GitHub en cada inicio
- Usa la imagen oficial `python:3.12-slim`
- Los secrets deben configurarse manualmente antes del despliegue
- El ingress usa Traefik con TLS automático via cert-manager
