# 使用 Python 3.9 作为基础镜像
FROM python:3.11

# 设置工作目录
WORKDIR /app

# 将 requirements.txt 复制到容器中
COPY requirements.txt .

# 更新 pip，安装依赖项，安装 FFmpeg，並清理 apt-get 產生的不必要文件
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variable for FFmpeg
ENV PATH="/usr/bin/ffmpeg:${PATH}"

# 将当前目录复制到容器中
COPY . .

RUN python manage.py collectstatic
ENV PORT=8000
# 运行 Django 服务器
CMD python manage.py runserver 0.0.0.0:$PORT
