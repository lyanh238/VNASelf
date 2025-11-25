# Hướng Dẫn Setup CI/CD với Docker Cloud Build

Hướng dẫn thiết lập CI/CD pipeline để tự động build và push Docker images lên các cloud registry.

## Mục Lục

1. [GitHub Actions với GHCR](#github-actions-với-ghcr)
2. [GitHub Actions với Docker Hub](#github-actions-với-docker-hub)
3. [AWS CodeBuild với ECR](#aws-codebuild-với-ecr)
4. [Google Cloud Build](#google-cloud-build)
5. [Azure DevOps](#azure-devops)

## GitHub Actions với GHCR

### Bước 1: Kích Hoạt GitHub Packages

1. Vào repository settings
2. Settings > Actions > General
3. Bật "Read and write permissions" cho GitHub Packages

### Bước 2: Sử Dụng Workflow Có Sẵn

File `.github/workflows/docker-build.yml` đã được tạo sẵn. Workflow này sẽ:
- Tự động build khi push lên `main` branch
- Build cho cả AMD64 và ARM64
- Push lên GitHub Container Registry (GHCR)
- Sử dụng build cache để tăng tốc

### Bước 3: Kiểm Tra

```bash
# Push code lên GitHub
git push origin main

# Xem workflow trong Actions tab
# https://github.com/your-username/your-repo/actions

# Pull image sau khi build xong
docker pull ghcr.io/your-username/your-repo:latest
```

### Cấu Hình Thêm

Nếu muốn thay đổi registry hoặc tags, chỉnh sửa `.github/workflows/docker-build.yml`:

```yaml
env:
  REGISTRY: ghcr.io  # Hoặc docker.io cho Docker Hub
  IMAGE_NAME: ${{ github.repository }}
```

## GitHub Actions với Docker Hub

### Bước 1: Tạo Docker Hub Secrets

1. Vào repository settings
2. Settings > Secrets and variables > Actions
3. Thêm 2 secrets:
   - `DOCKERHUB_USERNAME`: Tên đăng nhập Docker Hub
   - `DOCKERHUB_TOKEN`: Access token từ Docker Hub

### Bước 2: Tạo Docker Hub Access Token

1. Đăng nhập Docker Hub
2. Account Settings > Security > New Access Token
3. Copy token và lưu vào GitHub secret

### Bước 3: Sử Dụng Workflow

File `.github/workflows/docker-build-dockerhub.yml` đã được tạo sẵn.

### Bước 4: Kiểm Tra

```bash
# Push code
git push origin main

# Pull image từ Docker Hub
docker pull your-username/x23d8:latest
```

## AWS CodeBuild với ECR

### Bước 1: Tạo ECR Repository

```bash
aws ecr create-repository \
  --repository-name x23d8 \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true
```

### Bước 2: Tạo buildspec.yml

Tạo file `buildspec.yml` trong root project:

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '[{"name":"x23d8","imageUri":"%s"}]' $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG > imagedefinitions.json
```

### Bước 3: Tạo CodeBuild Project

1. Vào AWS Console > CodeBuild
2. Create build project
3. Cấu hình:
   - Source: GitHub
   - Environment: Docker
   - Service role: Tạo mới hoặc chọn existing
   - Buildspec: `buildspec.yml`

### Bước 4: Environment Variables

Thêm vào CodeBuild project:
- `AWS_ACCOUNT_ID`: Your AWS account ID
- `AWS_DEFAULT_REGION`: us-east-1
- `IMAGE_REPO_NAME`: x23d8

## Google Cloud Build

### Bước 1: Tạo cloudbuild.yaml

Tạo file `cloudbuild.yaml`:

```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/x23d8:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/x23d8:latest'
      - '.'

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'gcr.io/$PROJECT_ID/x23d8'

images:
  - 'gcr.io/$PROJECT_ID/x23d8:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/x23d8:latest'

options:
  machineType: 'E2_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY
```

### Bước 2: Kết Nối GitHub Repository

1. Vào Cloud Console > Cloud Build > Triggers
2. Create Trigger
3. Source: GitHub
4. Connect repository
5. Build configuration: Cloud Build configuration file
6. Location: `cloudbuild.yaml`

### Bước 3: Manual Build

```bash
# Submit build
gcloud builds submit --config cloudbuild.yaml .

# Hoặc build từ GitHub
gcloud builds submit --config cloudbuild.yaml https://github.com/your-username/your-repo
```

## Azure DevOps

### Bước 1: Tạo Azure Pipeline

Tạo file `azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  dockerRegistryServiceConnection: 'ACR-Connection'
  imageRepository: 'x23d8'
  containerRegistry: 'yourregistry.azurecr.io'
  dockerfilePath: '$(Build.SourcesDirectory)/Dockerfile'
  tag: '$(Build.BuildId)'

stages:
  - stage: Build
    displayName: Build and Push
    jobs:
      - job: Docker
        displayName: Build Docker Image
        steps:
          - task: Docker@2
            displayName: Build and push image
            inputs:
              command: buildAndPush
              repository: $(imageRepository)
              dockerfile: $(dockerfilePath)
              containerRegistry: $(dockerRegistryServiceConnection)
              tags: |
                $(tag)
                latest
```

### Bước 2: Tạo Service Connection

1. Project Settings > Service connections
2. New service connection > Docker Registry
3. Azure Container Registry
4. Chọn subscription và registry

### Bước 3: Chạy Pipeline

1. Pipelines > New pipeline
2. Chọn repository
3. Chọn `azure-pipelines.yml`
4. Run pipeline

## Multi-Platform Build

Để build cho cả AMD64 và ARM64:

### GitHub Actions

Workflow đã được cấu hình sẵn với:
```yaml
platforms: linux/amd64,linux/arm64
```

### Local Build

```bash
# Tạo builder
docker buildx create --name multiarch --use

# Build cho multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-username/x23d8:latest \
  --push .
```

## Best Practices

### 1. Sử Dụng Build Cache

Tất cả workflows đã được cấu hình với build cache:
- GitHub Actions: `cache-from: type=gha`
- Local: Sử dụng Docker layer cache

### 2. Semantic Versioning

Tag images với semantic versions:
```bash
docker tag x23d8:latest x23d8:1.0.0
docker tag x23d8:latest x23d8:1.0
docker tag x23d8:latest x23d8:latest
```

### 3. Security Scanning

Thêm security scanning vào workflow:

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### 4. Notifications

Thêm notifications khi build fail:

```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Build failed!'
```

## Troubleshooting

### Build Fails với "Out of Memory"

Tăng memory cho build:
```yaml
options:
  machineType: 'E2_HIGHCPU_8'  # Cho GCP
```

### Push Fails với "Unauthorized"

Kiểm tra:
- Secrets đã được set đúng chưa
- Token còn hạn không
- Permissions đã đủ chưa

### Multi-platform Build Chậm

Sử dụng buildx cache:
```bash
docker buildx build --cache-from type=registry,ref=your-registry/x23d8:buildcache .
```

---

**Lưu ý**: Đảm bảo không commit secrets vào repository. Luôn sử dụng GitHub Secrets, AWS Secrets Manager, hoặc các dịch vụ quản lý secrets khác.

