# Guía de Migración de Base de Datos: SQLite a PostgreSQL

Esta guía detalla los pasos para migrar la base de datos de **iWonder** desde SQLite (entorno de desarrollo actual) hacia PostgreSQL (entorno de producción recomendado).

## 1. Análisis del Esquema Actual
El sistema utiliza **SQLAlchemy ORM** con los siguientes modelos definidos en `back/infrastructure/db/models.py`:

| Modelo | Tabla | Columnas Clave | Notas |
|--------|-------|----------------|-------|
| `User` | `users` | `id`, `username`, `email`, `hashed_password` | Relaciones con Questions/Answers/Follows. |
| `Question` | `questions` | `id`, `content`, `asker_id`, `receiver_id` | Claves foráneas a `users`. |
| `Answer` | `answers` | `id`, `content`, `question_id`, `author_id` | Claves foráneas a `questions` y `users`. |
| `Follow` | `follows` | `follower_id`, `followed_id` | Tabla asociativa (Many-to-Many). |

### Mapeo de Tipos de Datos
| SQLite (Actual) | PostgreSQL (Destino) |
|-----------------|----------------------|
| `INTEGER` | `INTEGER` / `SERIAL` |
| `STRING` | `VARCHAR` |
| `TEXT` | `TEXT` |
| `BOOLEAN` | `BOOLEAN` |
| `DATETIME` | `TIMESTAMP WITH TIME ZONE` |

---

## 2. Prerrequisitos
Asegúrese de tener instalado:
1.  **PostgreSQL 13+** (Servidor activo).
2.  **pgAdmin** o cliente de terminal (`psql`).
3.  Librería `psycopg2` en el entorno Python:
    ```bash
    pip install psycopg2-binary
    ```

---

## 3. Pasos de Migración

### Paso 1: Preparar la Base de Datos PostgreSQL
1.  Conéctese a su servidor PostgreSQL.
2.  Cree una nueva base de datos vacía:
    ```sql
    CREATE DATABASE iwonder_db;
    ```
3.  Cree un usuario dedicado (opcional pero recomendado):
    ```sql
    CREATE USER iwonder_user WITH PASSWORD 'secure_password';
    GRANT ALL PRIVILEGES ON DATABASE iwonder_db TO iwonder_user;
    ```

### Paso 2: Generar Esquema en PostgreSQL
En lugar de exportar el SQL de SQLite (que puede ser incompatible), utilizaremos Alembic/SQLAlchemy para crear las tablas limpias.

1.  Modifique temporalmente la URL de conexión en `back/database.py` o configure la variable de entorno (ver Paso 4).
2.  Ejecute la aplicación brevemente o use Alembic para crear las tablas:
    ```bash
    # Opción A: Dejar que FastAPI cree las tablas al inicio (si models.Base.metadata.create_all está activo)
    # Opción B: Usar Alembic (Recomendado)
    alembic upgrade head
    ```

### Paso 3: Migración de Datos (Script Python)
Debido a las diferencias de sintaxis SQL, la forma más segura es usar un script de Python que lea de SQLite y escriba en PostgreSQL usando los modelos ORM.

Cree un archivo `migrate_data.py` en la carpeta `back/`:

```python
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Configuración
SQLITE_DB = "sql_app.db"
PG_HOST = "localhost"
PG_DB = "iwonder_db"
PG_USER = "iwonder_user"
PG_PASS = "secure_password"

def migrate():
    # 1. Conectar a SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sl_cursor = sqlite_conn.cursor()

    # 2. Conectar a PostgreSQL
    pg_conn = psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS)
    pg_cursor = pg_conn.cursor()

    tables = ["users", "questions", "answers", "follows"]
    
    try:
        for table in tables:
            print(f"Migrando tabla: {table}...")
            
            # Leer datos de SQLite
            sl_cursor.execute(f"SELECT * FROM {table}")
            rows = sl_cursor.fetchall()
            
            if not rows:
                continue

            # Obtener columnas
            columns = rows[0].keys()
            cols_str = ",".join(columns)
            placeholders = ",".join(["%s"] * len(columns))
            
            # Convertir filas a tuplas
            data = [tuple(row) for row in rows]
            
            # Insertar en Postgres
            query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
            execute_values(pg_cursor, query, data)
            
            # Ajustar secuencias (Auto-increment IDs)
            if "id" in columns:
                pg_cursor.execute(f"SELECT setval('{table}_id_seq', (SELECT MAX(id) FROM {table}));")
                
        pg_conn.commit()
        print("✅ Migración completada exitosamente.")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Error en migración: {e}")
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
```

### Paso 4: Actualizar Configuración de la Aplicación

Edite el archivo `back/database.py` para usar la variable de entorno o la nueva cadena de conexión:

**Antes:**
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
```

**Después:**
```python
import os
from dotenv import load_dotenv

load_dotenv() # Cargar .env

DB_USER = os.getenv("DB_USER", "iwonder_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secure_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "iwonder_db")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
```

Asegúrese de tener un archivo `.env`:
```ini
DB_USER=iwonder_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_NAME=iwonder_db
```

---

## 4. Validación Post-Migración

### Pruebas de Funcionalidad
1.  **Inicio de Sesión**: Intente loguearse con un usuario existente.
2.  **Crear Datos**: Publique una nueva pregunta y verifique que se guarde sin errores.
3.  **Integridad**: Verifique que las respuestas antiguas sigan asociadas a sus preguntas correspondientes.

### Validación de Rendimiento
1.  Ejecute consultas complejas (ej. Feed) y compare tiempos.
2.  Verifique índices:
    ```sql
    SELECT * FROM pg_indexes WHERE tablename = 'questions';
    ```
    Asegúrese de que existan índices en `asker_id`, `receiver_id`.

---

## 5. Plan de Rollback (Reversión)
Si algo falla críticamente:
1.  Restaure la configuración de `database.py` a SQLite.
2.  El archivo `sql_app.db` original permanece intacto en el servidor, por lo que el servicio puede restaurarse inmediatamente apuntando nuevamente a él.
