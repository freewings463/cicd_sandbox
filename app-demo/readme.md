# app-demo 单体应用

在 `cicd_sandbox/app-demo` 目录下是一个使用 **FastAPI + SQLAlchemy + PostgreSQL** 实现的简单用户服务，提供：

- 用户注册：`POST /users`
- 用户列表查询：`GET /users`

推荐使用 `docker compose` 一键启动应用和数据库。

## 前置条件

- 已安装 Docker
- 已安装 Docker Compose（最新版 Docker 一般自带 `docker compose` 子命令）

## 使用 docker-compose 启动

1. 进入项目目录：

   ```bash
   cd cicd_sandbox/app-demo
   ```

2. 构建并后台启动容器：

   ```bash
   docker compose up -d --build
   ```

   - 会启动两个服务：
     - `db`：PostgreSQL，容器端口 `5432`，映射到宿主机 `5433`
     - `web`：FastAPI 应用，容器端口 `8000`，映射到宿主机 `8000`

3. 查看服务运行状态（可选）：

   ```bash
   docker compose ps
   docker compose logs -f web
   ```

4. 访问接口：

   - Swagger 文档：<http://localhost:8000/docs>
   - 示例：
     - 注册用户：`POST http://localhost:8000/users`
       - 请求体示例：
         ```json
         {
           "username": "alice",
           "password": "secret123"
         }
         ```
     - 查询用户列表：`GET http://localhost:8000/users`

5. 停止并删除容器（可选）：

   ```bash
   docker compose down
   ```

## 可选：本地直接运行应用（不通过 Docker）

如果本地已有 Python 3.12+ 环境，也可以直接运行（仍需你自己准备一个 PostgreSQL 数据库，并保证环境变量与 `app/database.py` 中默认值一致或自行修改）：

```bash
cd cicd_sandbox/app-demo
pip install -r requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

然后同样访问：<http://localhost:8000/docs>。

