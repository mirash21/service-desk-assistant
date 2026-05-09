FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY admin_panel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY admin_panel/ ./admin_panel/
COPY utils/ ./utils/
COPY rag/ ./rag/

# Expose port
EXPOSE 8501

# Run Streamlit in production mode
CMD ["streamlit", "run", "admin_panel/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
