# Hướng Dẫn Đóng Gói và Triển Khai với Docker

Tài liệu này hướng dẫn cách đóng gói và triển khai toàn bộ hệ thống X23D8 sử dụng Docker.

## Mục Lục

1. [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
2. [Cài Đặt Docker](#cài-đặt-docker)
3. [Chuẩn Bị Môi Trường](#chuẩn-bị-môi-trường)
4. [Xây Dựng Docker Image](#xây-dựng-docker-image)
5. [Chạy Container](#chạy-container)
6. [Sử Dụng Docker Compose](#sử-dụng-docker-compose)
7. [Cấu Hình Nâng Cao](#cấu-hình-nâng-cao)
8. [Troubleshooting](#troubleshooting)

## Yêu Cầu Hệ Thống

- **Docker**: Phiên bản 20.10 trở lên
- **Docker Compose**: Phiên bản 2.0 trở lên (tùy chọn, nhưng khuyến nghị)
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- **Disk Space**: Tối thiểu 5GB trống

## Cài Đặt Docker

### Windows

1. Tải Docker Desktop từ [docker.com](https://www.docker.com/products/docker-desktop)
2. Cài đặt và khởi động Docker Desktop
3. Xác nhận cài đặt:
   ```powershell
   docker --version
   docker-compose --version
   ```

### macOS

```bash
# Sử dụng Homebrew
brew install --cask docker

# Hoặc tải từ docker.com
```

### Linux (Ubuntu/Debian)

```bash
# Cài đặt Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Thêm user vào docker group
sudo usermod -aG docker $USER

# Cài đặt Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout và login lại để áp dụng thay đổi
```

## Chuẩn Bị Môi Trường

### 1. Tạo File .env

Tạo file `.env` trong thư mục gốc của project:

```bash
# Copy từ template
cp env_template.txt .env
```

Chỉnh sửa file `.env` với các giá trị thực tế:

```env
# BẮT BUỘC
OPENAI_API_KEY=sk-your-actual-api-key-here

# TÙY CHỌN
OPENAI_MODEL=gpt-4o-mini
NEON_DATABASE_URL=postgresql://user:pass@host/db
TAVILY_API_KEY=your-tavily-key
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=x23d8
DEBUG_MCP=false
```

### 2. Chuẩn Bị Google Credentials (Nếu Cần)

Nếu sử dụng Google Calendar integration:

1. Tải file `credentials.json` từ Google Cloud Console
2. Đặt file trong thư mục gốc project
3. Cập nhật `GOOGLE_APPLICATION_CREDENTIALS` trong `.env` hoặc `docker-compose.yml`

## Xây Dựng Docker Image

### Cách 1: Sử Dụng Docker Build

```bash
# Build image
docker build -t x23d8:latest .

# Xem image đã build
docker images | grep x23d8
```

### Cách 2: Sử Dụng Docker Compose

```bash
# Build và start cùng lúc
docker-compose up --build

# Hoặc chỉ build
docker-compose build
```

## Chạy Container

### Cách 1: Chạy Trực Tiếp với Docker

```bash
# Chạy container
docker run -d \
  --name x23d8-app \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/backend/output:/app/backend/output \
  -v $(pwd)/backend/notes:/app/backend/notes \
  -v $(pwd)/backend/conversations:/app/backend/conversations \
  x23d8:latest

# Xem logs
docker logs -f x23d8-app

# Dừng container
docker stop x23d8-app

# Xóa container
docker rm x23d8-app
```

**Lưu ý cho Windows PowerShell:**
```powershell
# Thay $(pwd) bằng ${PWD} hoặc đường dẫn tuyệt đối
docker run -d `
  --name x23d8-app `
  -p 8000:8000 `
  --env-file .env `
  -v ${PWD}/uploads:/app/uploads `
  -v ${PWD}/backend/output:/app/backend/output `
  -v ${PWD}/backend/notes:/app/backend/notes `
  -v ${PWD}/backend/conversations:/app/backend/conversations `
  x23d8:latest
```

### Cách 2: Sử Dụng Docker Compose (Khuyến Nghị)

```bash
# Start services
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng services
docker-compose down

# Dừng và xóa volumes
docker-compose down -v

# Restart services
docker-compose restart
```

## Sử Dụng Docker Compose

### File docker-compose.yml

File `docker-compose.yml` đã được cấu hình sẵn với:

- **Port mapping**: 8000:8000
- **Environment variables**: Tự động load từ `.env`
- **Volume mounts**: Persist data directories
- **Health check**: Tự động kiểm tra sức khỏe container
- **Auto restart**: Tự động khởi động lại khi container crash

### Các Lệnh Thường Dùng

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f x23d8

# Rebuild và restart
docker-compose up -d --build

# Xem status
docker-compose ps

# Execute command trong container
docker-compose exec x23d8 bash

# Xem resource usage
docker-compose stats
```

## Cấu Hình Nâng Cao

### 1. Thay Đổi Port

Chỉnh sửa `docker-compose.yml`:

```yaml
services:
  x23d8:
    ports:
      - "3000:8000"  # Thay đổi port host từ 8000 sang 3000
```

### 2. Thêm Environment Variables

Có 2 cách:

**Cách 1: Thêm vào `.env`**
```env
NEW_VARIABLE=value
```

**Cách 2: Thêm vào `docker-compose.yml`**
```yaml
services:
  x23d8:
    environment:
      - NEW_VARIABLE=value
```

### 3. Mount Thêm Volumes

```yaml
services:
  x23d8:
    volumes:
      - ./custom-data:/app/custom-data
```

### 4. Resource Limits

```yaml
services:
  x23d8:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 5. Multi-Stage Build Optimization

Dockerfile đã sử dụng multi-stage build để:
- Giảm kích thước image cuối cùng
- Tách biệt quá trình build frontend và backend
- Tối ưu cache layers

## Docker Cloud Build

Build và push Docker images lên các cloud registry để dễ dàng deploy và chia sẻ.

### 1. Docker Hub

**Đăng ký và đăng nhập:**
```bash
# Đăng nhập Docker Hub
docker login

# Hoặc với username cụ thể
docker login -u your-username
```

**Build và Push:**
```bash
# Tag image với Docker Hub username
docker build -t your-username/x23d8:latest .
docker tag x23d8:latest your-username/x23d8:latest

# Push lên Docker Hub
docker push your-username/x23d8:latest

# Push với version tag
docker tag x23d8:latest your-username/x23d8:v1.0.0
docker push your-username/x23d8:v1.0.0
```

**Sử dụng image từ Docker Hub:**
```bash
# Pull và chạy
docker pull your-username/x23d8:latest
docker run -d -p 8000:8000 --env-file .env your-username/x23d8:latest
```

### 2. GitHub Container Registry (GHCR)

**Đăng nhập với GitHub Personal Access Token:**
```bash
# Tạo token tại: https://github.com/settings/tokens
# Quyền: write:packages, read:packages

echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

**Build và Push:**
```bash
# Tag với GHCR format
docker build -t ghcr.io/your-username/x23d8:latest .
docker tag x23d8:latest ghcr.io/your-username/x23d8:latest

# Push
docker push ghcr.io/your-username/x23d8:latest
```

**Cấu hình GitHub Actions (`.github/workflows/docker-build.yml`):**
```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags:
      - 'v*'

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to GHCR
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/x23d8:latest
            ghcr.io/${{ github.repository_owner }}/x23d8:${{ github.sha }}
          cache-from: type=registry,ref=ghcr.io/${{ github.repository_owner }}/x23d8:buildcache
          cache-to: type=registry,ref=ghcr.io/${{ github.repository_owner }}/x23d8:buildcache,mode=max
```

### 3. AWS Elastic Container Registry (ECR)

**Cài đặt AWS CLI:**
```bash
# Cài đặt AWS CLI
# Windows: https://aws.amazon.com/cli/
# Linux/Mac: pip install awscli

# Cấu hình credentials
aws configure
```

**Tạo ECR Repository:**
```bash
# Tạo repository
aws ecr create-repository --repository-name x23d8 --region us-east-1

# Lấy login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

**Build và Push:**
```bash
# Build
docker build -t x23d8:latest .

# Tag với ECR URI
docker tag x23d8:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/x23d8:latest

# Push
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/x23d8:latest
```

**Deploy với ECS/Fargate:**
```bash
# Pull và chạy local
docker pull YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/x23d8:latest
docker run -d -p 8000:8000 --env-file .env YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/x23d8:latest
```

### 4. Google Container Registry (GCR)

**Cài đặt Google Cloud SDK:**
```bash
# Cài đặt gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Đăng nhập
gcloud auth login
gcloud auth configure-docker
```

**Build và Push:**
```bash
# Build với GCR tag
docker build -t gcr.io/YOUR_PROJECT_ID/x23d8:latest .

# Push
docker push gcr.io/YOUR_PROJECT_ID/x23d8:latest
```

**Sử dụng Cloud Build (Khuyến nghị):**
```bash
# Submit build job
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/x23d8:latest .

# Hoặc sử dụng cloudbuild.yaml
```

**Tạo `cloudbuild.yaml`:**
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/x23d8:$SHORT_SHA', '-t', 'gcr.io/$PROJECT_ID/x23d8:latest', '.']
images:
  - 'gcr.io/$PROJECT_ID/x23d8:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/x23d8:latest'
options:
  machineType: 'E2_HIGHCPU_8'
```

**Deploy với Cloud Run:**
```bash
# Deploy
gcloud run deploy x23d8 \
  --image gcr.io/YOUR_PROJECT_ID/x23d8:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=your-key
```

### 5. Azure Container Registry (ACR)

**Cài đặt Azure CLI:**
```bash
# Cài đặt Azure CLI
# https://docs.microsoft.com/cli/azure/install-azure-cli

# Đăng nhập
az login
```

**Tạo ACR và Push:**
```bash
# Tạo resource group
az group create --name x23d8-rg --location eastus

# Tạo ACR
az acr create --resource-group x23d8-rg --name x23d8registry --sku Basic

# Đăng nhập vào ACR
az acr login --name x23d8registry

# Build và push
az acr build --registry x23d8registry --image x23d8:latest .
```

**Deploy với Azure Container Instances:**
```bash
az container create \
  --resource-group x23d8-rg \
  --name x23d8-container \
  --image x23d8registry.azurecr.io/x23d8:latest \
  --registry-login-server x23d8registry.azurecr.io \
  --registry-username x23d8registry \
  --registry-password YOUR_PASSWORD \
  --dns-name-label x23d8-app \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=your-key
```

### 6. Multi-Platform Build (ARM64 + AMD64)

Build image cho nhiều platform cùng lúc:

```bash
# Sử dụng Docker Buildx
docker buildx create --use --name multiarch-builder

# Build cho multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-username/x23d8:latest \
  --push .
```

### 7. CI/CD với Cloud Build

**GitHub Actions - Build và Push tự động:**

Tạo `.github/workflows/docker.yml`:
```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 8. Best Practices cho Cloud Build

1. **Sử dụng Build Cache:**
   ```bash
   docker buildx build --cache-from type=registry,ref=your-registry/x23d8:buildcache .
   ```

2. **Tag với Semantic Versioning:**
   ```bash
   docker tag x23d8:latest your-registry/x23d8:1.0.0
   docker tag x23d8:latest your-registry/x23d8:1.0
   docker tag x23d8:latest your-registry/x23d8:latest
   ```

3. **Scan Images cho Security:**
   ```bash
   # Sử dụng Trivy
   trivy image your-registry/x23d8:latest
   
   # Hoặc Docker Scout
   docker scout cves your-registry/x23d8:latest
   ```

4. **Sử dụng Build Secrets:**
   ```dockerfile
   # syntax=docker/dockerfile:1
   RUN --mount=type=secret,id=api_key \
       echo $api_key > /app/api_key.txt
   ```

5. **Multi-stage Build để giảm size:**
   - Đã được implement trong Dockerfile hiện tại

### 9. So Sánh Các Registry

| Registry | Free Tier | Pricing | Tốc Độ | Phù Hợp Cho |
|----------|-----------|---------|--------|-------------|
| Docker Hub | 1 private repo | $5/tháng cho unlimited | Trung bình | Personal projects |
| GHCR | Unlimited public | Free | Nhanh | Open source projects |
| AWS ECR | 500MB/tháng | $0.10/GB | Rất nhanh | AWS deployments |
| GCR | 0.5GB storage | $0.026/GB | Rất nhanh | GCP deployments |
| ACR | 1GB storage | $0.167/GB | Nhanh | Azure deployments |

## Troubleshooting

### 1. Container Không Khởi Động

**Kiểm tra logs:**
```bash
docker-compose logs x23d8
# hoặc
docker logs x23d8-app
```

**Kiểm tra environment variables:**
```bash
docker-compose exec x23d8 env | grep OPENAI
```

### 2. Lỗi "Port Already in Use"

```bash
# Tìm process đang dùng port 8000
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Thay đổi port trong docker-compose.yml
```

### 3. Lỗi "Permission Denied" trên Linux

```bash
# Fix permissions cho volumes
sudo chown -R $USER:$USER uploads/ backend/output/ backend/notes/
```

### 4. Frontend Không Load

- Kiểm tra xem frontend đã được build chưa trong Dockerfile
- Kiểm tra logs để xem có lỗi build không
- Đảm bảo `frontend/dist` được copy vào container

### 5. Backend Không Kết Nối Database

- Kiểm tra `NEON_DATABASE_URL` trong `.env`
- Đảm bảo database accessible từ container
- Kiểm tra network connectivity

### 6. OCR Không Hoạt Động

- Kiểm tra PaddlePaddle dependencies đã được cài đặt
- Xem logs để biết lỗi cụ thể
- Đảm bảo có đủ RAM (PaddlePaddle cần nhiều RAM)

### 7. Image Quá Lớn

```bash
# Xem kích thước image
docker images x23d8

# Sử dụng multi-stage build (đã có trong Dockerfile)
# Xóa unused images
docker image prune -a
```

### 8. Build Chậm

```bash
# Sử dụng build cache
docker-compose build --no-cache

# Hoặc build từng stage riêng
docker build --target frontend-builder -t x23d8-frontend .
docker build --target backend -t x23d8:latest .
```

## Production Deployment

### 1. Sử Dụng Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml x23d8
```

### 2. Sử Dụng Kubernetes

Tạo các file YAML cho Kubernetes:
- `deployment.yaml`
- `service.yaml`
- `configmap.yaml` (cho env vars)
- `secret.yaml` (cho API keys)

### 3. Sử Dụng Cloud Platforms

**AWS ECS/Fargate:**
- Build và push image lên ECR
- Tạo task definition với environment variables
- Deploy service

**Google Cloud Run:**
```bash
# Build và push
gcloud builds submit --tag gcr.io/PROJECT_ID/x23d8

# Deploy
gcloud run deploy x23d8 --image gcr.io/PROJECT_ID/x23d8
```

**Azure Container Instances:**
```bash
# Build và push
az acr build --registry REGISTRY_NAME --image x23d8:latest .

# Deploy
az container create --resource-group RESOURCE_GROUP --name x23d8 --image REGISTRY_NAME.azurecr.io/x23d8:latest
```

## Best Practices

1. **Không commit `.env` file**: Đã có trong `.gitignore`
2. **Sử dụng secrets management**: Sử dụng Docker secrets hoặc external secret managers
3. **Regular updates**: Cập nhật base images định kỳ
4. **Monitor resources**: Sử dụng `docker stats` để monitor
5. **Backup volumes**: Backup các volume quan trọng định kỳ
6. **Health checks**: Đã có health check trong Dockerfile
7. **Logging**: Sử dụng logging drivers cho production

## Liên Hệ và Hỗ Trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs: `docker-compose logs`
2. Xem troubleshooting section ở trên
3. Tạo issue trên GitHub repository

---

**Lưu ý**: File `.env` chứa thông tin nhạy cảm, không bao giờ commit vào Git!

