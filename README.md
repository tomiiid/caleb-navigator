# Caleb Navigator

A campus navigation web application built with a **Django REST Framework** backend and a **Vue 3** frontend. It uses Dijkstra's algorithm for shortest-path routing and displays interactive maps via Leaflet.js.

---

## Project Structure

```
caleb-navigator/
+-- backend/          # Django REST API
|   +-- config/       # Django settings, URLs, WSGI/ASGI
|   +-- navigation/   # Navigation app (models, views, Dijkstra logic)
|   +-- users/        # Custom user model & JWT auth
|   +-- manage.py
|   +-- .env          # Environment variables (not committed)
+-- frontend/         # Vue 3 + Vite SPA
    +-- src/          # Vue components, router, stores
    +-- public/
    +-- index.html
```

---

## Prerequisites

| Tool    | Minimum Version          |
|---------|--------------------------|
| Python  | 3.10+                    |
| pip     | latest                   |
| Node.js | 20.19.0 or >= 22.12.0    |
| npm     | 9+                       |

---

## Backend Setup (Django)

### 1. Navigate to the backend folder

```bash
cd backend
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the `.env` file

Create a file at `backend/.env` with the following content:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

> **Note:** Never commit your `.env` file. It is already listed in `.gitignore`.

To generate a secure `SECRET_KEY`, run:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. (Optional) Create a superuser for the Django admin

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

The API will be available at: **`http://127.0.0.1:8000/`**

---

## Frontend Setup (Vue 3 + Vite)

### 1. Navigate to the frontend folder

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Start the development server

```bash
npm run dev
```

The app will be available at: **`http://localhost:5173/`**

---

## API & CORS

The Django backend is pre-configured to allow requests from the Vue dev server:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

If you change the frontend port, update `CORS_ALLOWED_ORIGINS` in `backend/config/settings.py`.

---

## Authentication

This project uses **JWT (JSON Web Tokens)** via `djangorestframework-simplejwt`.

| Token         | Lifetime    |
|---------------|-------------|
| Access Token  | 30 minutes  |
| Refresh Token | 1 day       |

Tokens are passed as `Bearer <token>` in the `Authorization` header.

---

## Database

SQLite is used for development and stored at `backend/db.sqlite3`.
No additional database setup is required for local development.

---

## Running Both Servers

Open **two separate terminals**:

**Terminal 1 - Backend:**

```bash
cd backend
venv\Scripts\activate      # Windows
python manage.py runserver
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

Then open your browser at **`http://localhost:5173`**.

---

## Available Scripts

### Backend

| Command                            | Description                    |
|------------------------------------|--------------------------------|
| `python manage.py runserver`       | Start dev server               |
| `python manage.py migrate`         | Apply database migrations      |
| `python manage.py createsuperuser` | Create admin user              |
| `python manage.py makemigrations`  | Generate migration files       |

### Frontend

| Command           | Description              |
|-------------------|--------------------------|
| `npm run dev`     | Start Vite dev server    |
| `npm run build`   | Build for production     |
| `npm run preview` | Preview production build |
| `npm run lint`    | Lint & auto-fix code     |
| `npm run format`  | Format source with Prettier |

---

## Key Dependencies

### Backend

- [Django](https://www.djangoproject.com/) - Web framework
- [Django REST Framework](https://www.django-rest-framework.org/) - API toolkit
- [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/) - JWT authentication
- [django-cors-headers](https://github.com/adamchainz/django-cors-headers) - CORS support

### Frontend

- [Vue 3](https://vuejs.org/) - UI framework
- [Vue Router](https://router.vuejs.org/) - Client-side routing
- [Pinia](https://pinia.vuejs.org/) - State management
- [Axios](https://axios-http.com/) - HTTP client
- [Leaflet](https://leafletjs.com/) + [@vue-leaflet/vue-leaflet](https://github.com/vue-leaflet/vue-leaflet) - Interactive maps
- [Vite](https://vitejs.dev/) - Build tool

---

## What is Excluded from Version Control

The following are listed in `.gitignore` and should **not** be committed:

```
backend/venv/          # Python virtual environment
backend/__pycache__/   # Python bytecode cache
backend/.env           # Secret environment variables
frontend/node_modules/ # Node dependencies
frontend/dist/         # Production build output
```