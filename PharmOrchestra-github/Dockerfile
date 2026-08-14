# ============================================================
# Dockerfile - PharmOrchestra 容器配置
# 用大白话说：这个文件告诉Docker怎么打包和运行我们的程序
# ============================================================

# 使用Python官方镜像（精简版）
FROM python:3.11-slim

# 设置工作目录（程序在容器里运行的目录）
WORKDIR /app

# 把项目所有文件复制到容器的/app目录
COPY . /app/

# 安装依赖（目前只需要pytest，可选）
RUN pip install --no-cache-dir pytest>=7.0.0 || true

# 设置Python环境变量，确保输出不缓冲（实时显示print）
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# 默认命令：运行main.py，默认疾病是糖尿病
CMD ["python", "main.py", "糖尿病"]
