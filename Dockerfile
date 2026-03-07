# Dockerfile for LaTeX + Python + Snakemake CI
FROM debian:bookworm-slim

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-full \
    biber \
    python3 \
    python3-pip \
    python3-venv \
    python3-pygments \
    git \
    make \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /workspace

# 3. Pre-install dependencies from requirements.txt (if it changes, image rebuilds)
# We copy it here so that the 'pip install' step is cached.
COPY requirements.txt .
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# 4. Final configuration
CMD ["bash"]
