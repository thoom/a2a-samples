# A2A mTLS POC Makefile
# This Makefile provides targets for deploying A2A agents with mTLS authentication

.PHONY: all clean help check-prereqs
.PHONY: images deploy test-k8s
.PHONY: logs port-forward cleanup

# Default target
all: check-prereqs images deploy test-k8s

# Configuration
NAMESPACE := default

# Help target
help:
	@echo "A2A mTLS POC Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  all              - Complete deployment (images, deploy, test)"
	@echo "  check-prereqs    - Check if required tools are available"
	@echo "  images           - Build Docker images"
	@echo "  deploy           - Deploy to Kubernetes"
	@echo "  test-k8s         - Test Kubernetes deployment"
	@echo "  logs             - Show logs from both services"
	@echo "  port-forward     - Forward demo-ui port to localhost:12000"
	@echo "  cleanup          - Remove all resources and clean up"
	@echo "  clean            - Remove generated images"
	@echo "  help             - Show this help message"
	@echo ""
	@echo "Environment variables:"
	@echo "  GOOGLE_API_KEY   - Your Google API key (required for agents)"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Kubernetes secrets must be created externally:"
	@echo "    - google-api-secret (with api-key)"
	@echo ""
	@echo "Examples:"
	@echo "  make all                    # Complete deployment"
	@echo "  make images deploy          # Build and deploy"
	@echo "  make test-k8s               # Test deployment"
	@echo "  make cleanup                # Clean everything"

# Check prerequisites
check-prereqs:
	@echo "Checking prerequisites..."
	@command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl is not installed or not in PATH"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "Error: docker is not installed or not in PATH"; exit 1; }
	@command -v openssl >/dev/null 2>&1 || { echo "Error: openssl is not installed or not in PATH"; exit 1; }
	@kubectl cluster-info >/dev/null 2>&1 || { echo "Error: Cannot connect to Kubernetes cluster"; exit 1; }
	@echo "✅ Prerequisites check passed!"

# Build Docker images
images:
	@echo "Building Docker images..."
	@docker build -t a2a-demo-ui:latest -f Dockerfile.demo-ui ..
	@docker build -t a2a-google-adk-agent:latest -f Dockerfile.google-adk-agent ..
	@echo "✅ Docker images built successfully!"

# Deploy to Kubernetes
deploy:
	@echo "Deploying to Kubernetes..."
	@echo "⚠️  Ensuring required secrets exist..."
	@if ! kubectl get secret google-api-secret -n $(NAMESPACE) >/dev/null 2>&1; then \
		echo "❌ Error: google-api-secret not found. Please create it externally."; \
		exit 1; \
	fi
	@echo "✅ All required secrets found"
	@kubectl apply -f demo-ui-pod.yaml
	@kubectl apply -f google-adk-agent-pod.yaml
	@echo "✅ Deployed to Kubernetes!"
	@echo ""
	@echo "Waiting for pods to be ready..."
	@kubectl wait --for=condition=ready pod -l app=demo-ui -n $(NAMESPACE) --timeout=60s
	@kubectl wait --for=condition=ready pod -l app=google-adk-agent -n $(NAMESPACE) --timeout=60s
	@echo "✅ Pods are ready!"

# Test Kubernetes deployment
test-k8s:
	@echo "=== A2A Kubernetes Testing ==="
	@echo ""
	@echo "1. Checking pod status..."
	@DEMO_UI_POD=$$(kubectl get pod demo-ui -n $(NAMESPACE) -o jsonpath='{.metadata.name}' 2>/dev/null || echo ""); \
	GOOGLE_ADK_POD=$$(kubectl get pod google-adk-agent -n $(NAMESPACE) -o jsonpath='{.metadata.name}' 2>/dev/null || echo ""); \
	if [ -z "$$DEMO_UI_POD" ]; then \
		echo "❌ Demo UI pod not found"; \
		exit 1; \
	else \
		DEMO_UI_STATUS=$$(kubectl get pod demo-ui -n $(NAMESPACE) -o jsonpath='{.status.phase}'); \
		if [ "$$DEMO_UI_STATUS" = "Running" ]; then \
			echo "✅ Demo UI pod is running: demo-ui"; \
		else \
			echo "⚠️  Demo UI pod status: $$DEMO_UI_STATUS"; \
		fi; \
	fi; \
	if [ -z "$$GOOGLE_ADK_POD" ]; then \
		echo "❌ Google ADK agent pod not found"; \
		exit 1; \
	else \
		GOOGLE_ADK_STATUS=$$(kubectl get pod google-adk-agent -n $(NAMESPACE) -o jsonpath='{.status.phase}'); \
		if [ "$$GOOGLE_ADK_STATUS" = "Running" ]; then \
			echo "✅ Google ADK agent pod is running: google-adk-agent"; \
		else \
			echo "⚠️  Google ADK agent pod status: $$GOOGLE_ADK_STATUS"; \
		fi; \
	fi
	@echo ""
	@echo "2. Checking secrets..."
	@for secret in demo-ui-tls google-adk-agent-tls google-api-secret; do \
		if kubectl get secret $$secret -n $(NAMESPACE) >/dev/null 2>&1; then \
			echo "✅ Secret $$secret exists"; \
		else \
			echo "❌ Secret $$secret missing"; \
		fi; \
	done
	@echo ""
	@echo "3. Testing service connectivity..."
	@kubectl run test-demo-ui --image=curlimages/curl:latest --rm -i --restart=Never -n $(NAMESPACE) -- \
		curl -s -o /dev/null -w "%{http_code}" http://demo-ui:12000 || echo "Failed to connect to Demo UI"
	@kubectl run test-google-adk --image=curlimages/curl:latest --rm -i --restart=Never -n $(NAMESPACE) -- \
		curl -s -o /dev/null -w "%{http_code}" http://google-adk-agent:10002 || echo "Failed to connect to Google ADK agent"
	@echo "✅ Kubernetes deployment test complete!"

# Show logs
logs:
	@echo "=== Service Logs ==="
	@echo ""
	@echo "Demo UI logs (last 20 lines):"
	@kubectl logs --tail=20 pod/demo-ui -n $(NAMESPACE) 2>/dev/null || echo "Could not retrieve Demo UI logs"
	@echo ""
	@echo "Google ADK agent logs (last 20 lines):"
	@kubectl logs --tail=20 pod/google-adk-agent -n $(NAMESPACE) 2>/dev/null || echo "Could not retrieve Google ADK agent logs"

# Follow logs
logs-follow:
	@echo "Following logs (Ctrl+C to stop)..."
	@kubectl logs -f pod/demo-ui -n $(NAMESPACE) &
	@kubectl logs -f pod/google-adk-agent -n $(NAMESPACE) &
	@wait

# Port forward Demo UI
port-forward:
	@echo "Port forwarding Demo UI to localhost:12000..."
	@echo "Access at: https://localhost:12000"
	@echo "Press Ctrl+C to stop"
	@kubectl port-forward service/demo-ui 12000:12000 -n $(NAMESPACE)

# Clean up everything
cleanup:
	@echo "Cleaning up A2A deployment..."
	@kubectl delete -f demo-ui-pod.yaml --ignore-not-found=true
	@kubectl delete -f google-adk-agent-pod.yaml --ignore-not-found=true
	@echo "⚠️  Note: Secrets are managed externally and will not be deleted"
	@echo "✅ Kubernetes resources removed"
	@$(MAKE) clean

# Clean local artifacts
clean:
	@echo "Cleaning local artifacts..."
	@docker rmi a2a-demo-ui:latest a2a-google-adk-agent:latest 2>/dev/null || true
	@echo "✅ Local cleanup complete"

# Status check
status:
	@echo "=== A2A Status ==="
	@echo ""
	@echo "Pods:"
	@kubectl get pods -n $(NAMESPACE) -l 'app in (demo-ui,google-adk-agent)' 2>/dev/null || echo "No pods found"
	@echo ""
	@echo "Services:"
	@kubectl get services -n $(NAMESPACE) -l 'app in (demo-ui,google-adk-agent)' 2>/dev/null || echo "No services found"
	@echo ""
	@echo "Secrets:"
	@kubectl get secrets -n $(NAMESPACE) | grep -E '(google-api-secret)' 2>/dev/null || echo "No secrets found"
	@echo ""
	@echo "Docker images:"
	@docker images | grep a2a- || echo "No A2A images found"
