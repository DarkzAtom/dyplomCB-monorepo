FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run without --reload (reload=True in frontend.py is for local dev only).
CMD ["uvicorn", "frontend:app", "--host", "0.0.0.0", "--port", "8000"]
