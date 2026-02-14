# iWonder

iWonder es una plataforma social de preguntas y respuestas anónimas (estilo NGL/Ask.fm) que conecta a las personas a través de la curiosidad.

## Tecnologías Utilizadas

### Backend
- **Lenguaje**: Python
- **Framework**: FastAPI
- **Base de Datos**: PostgreSQL
- **ORM**: SQLAlchemy + Alembic

### Frontend
- **Framework**: Next.js (React)
- **Estilos**: Tailwind CSS
- **Lenguaje**: TypeScript

## Requisitos Previos

- Python 3.x
- Node.js & npm
- PostgreSQL (corriendo en local en el puerto 5432)

## Instrucciones de Ejecución

### 1. Configuración de Base de Datos
Asegúrate de tener PostgreSQL corriendo y crea una base de datos llamada `iwonder`.
El sistema espera las credenciales por defecto (usuario: `postgres`, contraseña: `postgres`). Si son diferentes, ajusta el archivo `back/.env`.

### 2. Ejecutar el Backend
Desde la raíz del proyecto:

```bash
# Instalar dependencias
cd back
pip install -r requirements.txt
# Ejecutar migraciones (crear tablas)

alembic upgrade head

# Iniciar servidor
uvicorn main:app --reload
```
El backend estará disponible en: http://127.0.0.1:8000
Documentación interactiva: http://127.0.0.1:8000/docs

### 3. Ejecutar el Frontend
Desde la raíz del proyecto:

```bash
cd front

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```
El frontend estará disponible en: http://localhost:3000

## Podman

### Requisitos
- Podman
- Podman Compose

### Paso a paso

1. Crear el archivo .env en la raíz del proyecto.
2. Iniciar la máquina de Podman.
3. Levantar el stack con compose.

Desde la raíz del proyecto:

```bat
podman machine start
podman compose -f podman-compose.yml up --build
```

### Detener servicios

```bat
podman compose -f podman-compose.yml down
```

Servicios:
- Backend: http://127.0.0.1:8000
- Frontend: http://localhost:3000
