```bash
# 中文注释：创建 CI 工作流文件，兼顾缓存迁移与 Node22/24 切换；调度到内网 self-hosted runner 以访问 Harbor
cat > .github/workflows/build-and-push.yaml <<'EOF'
# 工作流显示名称，便于在 Actions 列表中识别
name: build-and-push # 单仓库镜像构建与推送

# 触发条件：push 到 main 或手动触发
on:
  # push 触发，限定 main 分支
  push:
    branches: [ main ]
  # 手动触发入口，便于重试/快速回滚
  workflow_dispatch: {}

# 全局环境变量，引用 Secrets 避免硬编码
env:
  IMAGE_REGISTRY: ${{ secrets.HARBOR_REGISTRY }} # 引用已经通过gh set命令设置在仓库中的 Harbor 内网域名或 IP（例：10.107.131.6）
  IMAGE_PROJECT:  ${{ secrets.HARBOR_PROJECT }}  # 引用已经通过gh set命令设置在仓库中的 Harbor 项目
  IMAGE_NAME: app-demo                           # 镜像名，建议与仓库一致

jobs:
  # 单一 job，负责构建并推送镜像
  docker:
    runs-on: [self-hosted, linux, x64, harbor-local] # 调度到本地自托管 runner，具备内网 Harbor 访问
    permissions:
      contents: read   # 仅读取代码即可
      packages: write  # 允许写入缓存/GHCR 以支持 Buildx 缓存
    steps:
      # Step1 拉取代码
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # 保留完整 git 历史，方便标签/追溯

      # Step2 准备 Python 运行时（CI 里执行 FastAPI 单元测试）
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # Step3 单元测试，失败则终止流水线；使用 SQLite 避免依赖外部 Postgres
      - name: Run unit tests
        working-directory: app-demo
        env:
          DATABASE_URL: sqlite:///./test_app.db
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
          pytest

      # Step4 初始化 Buildx（支持多架构与缓存导出）
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      # Step5 登录 Harbor，后续构建/推送需要凭证
      - name: Login to Harbor
        uses: docker/login-action@v3
        with:
          registry: ${{ env.IMAGE_REGISTRY }} # Harbor 地址（内网）
          username: ${{ secrets.HARBOR_USERNAME }} # 机器人账户
          password: ${{ secrets.HARBOR_PASSWORD }} # 机器人 Token

      # Step6 构建并推送镜像，启用 GHA 缓存与供应链元数据
      - name: Build and push image (with cache)
        uses: docker/build-push-action@v6
        with:
          context: ./app-demo # 构建上下文指向应用目录
          file: ./app-demo/Dockerfile
          push: true # 构建完成后推送到 Harbor
          tags: |
            # latest 用于默认部署/快速回滚
            ${{ env.IMAGE_REGISTRY }}/${{ env.IMAGE_PROJECT }}/${{ env.IMAGE_NAME }}:latest
            # 以 commit SHA 标记，便于精确回溯
            ${{ env.IMAGE_REGISTRY }}/${{ env.IMAGE_PROJECT }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha # 读取 GitHub Actions Cache v2，加速冷启动
          cache-to: type=gha,mode=max # 将所有层写入新缓存后端供后续命中
          labels: |
            org.opencontainers.image.source=${{ github.repository }} # 镜像溯源到仓库
            org.opencontainers.image.revision=${{ github.sha }}       # 记录具体 commit
          sbom: true # 生成 SBOM 供漏洞/合规扫描
          provenance: true # 生成 SLSA provenance 证明供应链完整性
EOF
```
