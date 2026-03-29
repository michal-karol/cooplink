FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Node.js and npm - django-tailwind needs them to build CSS.
RUN apt-get update \
    && apt-get install -y nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Install frontend dependencies first to improve Docker layer caching.
COPY theme/static_src/package.json theme/static_src/package-lock.json ./theme/static_src/
RUN cd theme/static_src && npm install

COPY . .

# Build Tailwind CSS and collect static files for deployment.
RUN python manage.py tailwind build
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]