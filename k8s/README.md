# A2A Samples mTLS POC

This directory contains the necessary files to deploy A2A agents with mutual TLS (mTLS) authentication in a Kubernetes cluster using the default namespace.

## Overview

The mTLS implementation provides secure communication between:
- **Demo UI** (`demo-ui-mtls.py`) - Web interface running on port 12000
- **Google ADK Agent** (`google-adk-agent-mtls.py`) - Agent service running on port 10002

## Prerequisites

- Kubernetes cluster with `kubectl` access
- Docker for building container images
- OpenSSL for certificate generation
- Google API key for the Google ADK agent

## Quick Start

**Prerequisites:** You must create the required Kubernetes secrets externally before deployment.

1. **Create required secrets externally:**
   - `demo-ui-tls` (with `client.crt`, `client.key`, `ca.crt`)
   - `google-adk-agent-tls` (with `client.crt`, `client.key`, `ca.crt`)  
   - `google-api-secret` (with `api-key`)

2. **Deploy everything:**
   ```bash
   make all
   ```

3. **Access the demo UI:**
   ```bash
   make port-forward
   ```
   Then open https://localhost:12000 in your browser.

4. **View status and logs:**
   ```bash
   make status
   make logs
   ```

## Manual Deployment Steps

If you prefer to run the deployment steps manually:

### 1. Create Kubernetes Secrets (External)
Create the required secrets in your Kubernetes cluster:
- `demo-ui-tls` - containing `client.crt`, `client.key`, `ca.crt`
- `google-adk-agent-tls` - containing `client.crt`, `client.key`, `ca.crt`
- `google-api-secret` - containing `api-key`

### 2. Build Docker Images
```bash
make images
```

### 3. Deploy to Kubernetes
```bash
make deploy
```

### 4. Test the Deployment
```bash
make test-k8s
```

## Available Make Targets

```bash
make help          # Show all available targets
make all            # Complete deployment (images, deploy, test)
make check-prereqs  # Check if required tools are available
make images         # Build Docker images
make deploy         # Deploy to Kubernetes
make test-local     # Test mTLS implementation locally (requires external certs)
make test-k8s       # Test Kubernetes deployment
make logs           # Show logs from both services
make logs-follow    # Follow logs in real-time
make port-forward   # Forward demo-ui port to localhost:12000
make status         # Show current deployment status
make cleanup        # Remove all resources and clean up
make clean          # Remove generated images
```

## Files Description

### Core Files
- `Makefile` - **Main automation** - all deployment and management tasks
- `demo-ui-mtls.py` - mTLS-enabled demo UI application
- `google-adk-agent-mtls.py` - mTLS-enabled Google ADK agent

### Kubernetes Manifests
- `demo-ui-pod.yaml` - Demo UI pod and service
- `google-adk-agent-pod.yaml` - Google ADK agent pod and service

### Docker Files
- `Dockerfile.demo-ui` - Demo UI container image definition
- `Dockerfile.google-adk-agent` - Google ADK agent container image definition

### Documentation
- `README.md` - Comprehensive deployment and usage guide
- `IMPLEMENTATION-SUMMARY.md` - Technical details and architecture

## Certificate Structure

The certificates are organized as follows:
```
certs/
├── ca/
│   ├── ca.crt          # CA certificate
│   └── ca.key          # CA private key
├── demo-ui/
│   ├── tls.crt         # Demo UI certificate
│   └── tls.key         # Demo UI private key
└── google-adk-agent/
    ├── tls.crt         # Google ADK agent certificate
    └── tls.key         # Google ADK agent private key
```

Kubernetes secrets structure:
```
demo-ui-tls secret:
├── client.crt          # Demo UI certificate (from tls.crt)
├── client.key          # Demo UI private key (from tls.key)
└── ca.crt              # CA certificate

google-adk-agent-tls secret:
├── client.crt          # Google ADK agent certificate (from tls.crt)
├── client.key          # Google ADK agent private key (from tls.key)
└── ca.crt              # CA certificate
```

## Kubernetes Secrets

The following secrets are created in the default namespace:
- `demo-ui-tls` - Contains Demo UI client certificate (`client.crt`), private key (`client.key`), and CA certificate (`ca.crt`)
- `google-adk-agent-tls` - Contains Google ADK agent client certificate (`client.crt`), private key (`client.key`), and CA certificate (`ca.crt`)
- `google-api-secret` - Contains Google API key (you need to update this)

## Testing

### Local Testing (Recommended First)
Before deploying to Kubernetes, you can test the mTLS implementation locally:

```bash
make test-local
```

This will start both services locally and verify that mTLS is working correctly.

### Kubernetes Testing
After deployment to Kubernetes:

```bash
make test-k8s
```

This will:
- Check pod status
- Verify secrets exist
- Test service connectivity
- Show recent logs

## Troubleshooting

### Check Pod Status
```bash
make status
```

### View Logs
```bash
# Show recent logs
make logs

# Follow logs in real-time
make logs-follow
```

### Verify Secrets
```bash
kubectl get secrets -n default | grep -E '(demo-ui-tls|google-adk-agent-tls)'
```

### Test mTLS Connection
```bash
# Port forward to demo UI
make port-forward &

# Test with curl (you'll need the client certificates)
curl --cert certs/demo-ui/tls.crt --key certs/demo-ui/tls.key --cacert certs/ca/ca.crt https://localhost:12000
```

## Security Notes

- This is a POC setup using self-signed certificates
- Certificates are valid for 365 days
- Private keys are stored in Kubernetes secrets with restricted permissions (mode 0400)
- For production, use proper certificate management (cert-manager, HashiCorp Vault, etc.)

## mTLS Configuration

Both services are configured with:
- TLS 1.2+ enforcement
- Client certificate verification
- Proper certificate validation
- Environment variable-based certificate paths

The mTLS implementation includes:
- Server-side certificate presentation
- Client-side certificate verification
- Mutual authentication between services
- Secure communication channels

## Cleanup

To remove the deployment:
```bash
make cleanup
```

This will remove:
- Kubernetes deployments and services
- Kubernetes secrets  
- Generated certificates
- Docker images
