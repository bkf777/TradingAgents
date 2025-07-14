# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将依赖文件复制到工作目录
COPY requirements.txt .

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码到工作目录
COPY . .

# 暴露端口
EXPOSE 5000

# 运行应用的命令
CMD ["python", "api_server_simple.py"]
