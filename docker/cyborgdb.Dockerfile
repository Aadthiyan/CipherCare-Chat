FROM cyborginc/cyborgdb-service:latest

# CyborgDB Service - Encrypted Vector Database
ENV PORT=8002

EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=5 \
    CMD curl -f http://localhost:8002/v1/health || exit 1

# Use the image's default CMD
