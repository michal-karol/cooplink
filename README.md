# CoopLink

CoopLink is a Django app for collecting, organizing, and sharing useful links. Users can keep a private library, pin important items to a dashboard, and publish selected links to a shared feed for other users.

## Features

- User registration and login
- Optional email OTP during sign-up and login
- Cloudflare Turnstile on registration and password login
- Password reset by email
- Personal link library with search and category filtering
- Shared dashboard for public links
- Pin and unpin actions for quick access
- Category management
- Django admin for internal management

## Stack

- Python 3.12
- Django 6
- PostgreSQL 17
- Tailwind CSS 4
- DaisyUI 5
- Docker Compose

## Prerequisites

For local development without Docker:

- Python 3.12
- Node.js and npm
- PostgreSQL

For the containerized workflow:

- Docker
- Docker Compose

## Environment Variables

Copy the example file and adjust values as needed:

```bash
cp .env.example .env
```

Important variables:

- `SECRET_KEY`: required, must be a real random secret
- `DEBUG`: `True` for local development, `False` for production
- `ALLOWED_HOSTS`: comma-separated hostnames
- `CSRF_TRUSTED_ORIGINS`: comma-separated full origins such as `https://example.com`
- `DATABASE_URL`: PostgreSQL connection string for local non-Docker runs
- `TEST_DATABASE_URL`: optional separate test database
- `CLOUDFLARE_TURNSTILE_*` or `TURNSTILE_*`: required Turnstile site and secret keys
- `MAILTRAP_*` or `EMAIL_*`: email backend credentials

Notes:

- In Docker Compose, `DATABASE_URL` is overridden for the `web` container to use the `db` service.
- `.env` is excluded from the Docker build context, so secrets are not baked into the image.

## Local Development

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd cooplink
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Create the env file

```bash
cp .env.example .env
```

Then edit `.env` and set at least:

- `SECRET_KEY`
- `DATABASE_URL`
- Turnstile site and secret keys

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Install frontend dependencies

```bash
cd theme/static_src
npm install
cd ../..
```

### 6. Start PostgreSQL

If you want to run only the database in Docker:

```bash
docker compose up -d db
```

### 7. Apply migrations

```bash
python manage.py migrate
```

### 8. Create a superuser

```bash
python manage.py createsuperuser
```

### 9. Run the app

Terminal 1:

```bash
python manage.py runserver
```

Terminal 2:

```bash
python manage.py tailwind start
```

The app will be available at `http://127.0.0.1:8000`.

## Docker Compose

Start the full stack:

```bash
docker compose up --build
```

This starts:

- `db`: PostgreSQL 17
- `web`: Django app with migrations applied on startup

Stop the stack:

```bash
docker compose down
```

Remove containers and the database volume:

```bash
docker compose down -v
```

The app will be available at `http://127.0.0.1:8000`.

## Kubernetes / K3s

A sample manifest is included at [`deploy/k8s/cooplink.yaml`](deploy/k8s/cooplink.yaml).

Before applying it:

- replace `your-dockerhub-user/cooplink:latest` with your published image
- replace the placeholder secret values
- set real `TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY`

Apply the manifest:

```bash
kubectl apply -f deploy/k8s/cooplink.yaml
```

Check the deployment:

```bash
kubectl get pods
kubectl get svc
```

## Running Tests

Run the Django test suite:

```bash
python manage.py test
```

If `TEST_DATABASE_URL` is not set, tests fall back to SQLite. CI uses PostgreSQL.

## CI

GitHub Actions runs on pushes to `main` and on pull requests. The workflow:

- sets up Python 3.12
- starts PostgreSQL 17
- installs dependencies
- runs migrations
- runs the Django test suite

The workflow file is at [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Project Structure

```text
apps/
  accounts/    Authentication, profile, OTP, password reset
  links/       Link library, dashboards, categories
config/        Django settings and root URLs
theme/         Tailwind and shared templates
compose.yaml   Local container orchestration
Dockerfile     Web image build
```
