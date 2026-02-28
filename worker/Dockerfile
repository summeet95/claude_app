FROM python:3.11-slim

# System deps: ffmpeg, OpenGL (for trimesh/osmesa)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libosmesa6 \
    libosmesa6-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

ENV PYOPENGL_PLATFORM=osmesa

CMD ["./entrypoint.sh"]
