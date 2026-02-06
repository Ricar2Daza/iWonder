import sqlite3
import shutil
import os
import time

DB_PATH = "sql_app.db"
BACKUP_DIR = "backups"

def maintenance():
    print("--- Inicio de Mantenimiento de Base de Datos ---")
    
    # 1. Verificar existencia
    if not os.path.exists(DB_PATH):
        print(f"Error: No se encuentra la base de datos en {DB_PATH}")
        return

    # 2. Crear directorio de backups si no existe
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Directorio de backups creado: {BACKUP_DIR}")

    # 3. Realizar Respaldo
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_filename = f"sql_app_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Respaldo creado exitosamente: {backup_path}")
    except Exception as e:
        print(f"❌ Error al crear respaldo: {e}")
        return

    # 4. Conectar y Optimizar
    print("Iniciando optimización (VACUUM)...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Obtener tamaño antes
        size_before = os.path.getsize(DB_PATH)
        
        # Ejecutar VACUUM
        cursor.execute("VACUUM")
        conn.close()
        
        # Obtener tamaño después
        size_after = os.path.getsize(DB_PATH)
        
        print(f"✅ Base de datos optimizada exitosamente.")
        print(f"Tamaño antes: {size_before / 1024:.2f} KB")
        print(f"Tamaño después: {size_after / 1024:.2f} KB")
        print(f"Espacio recuperado: {(size_before - size_after) / 1024:.2f} KB")
        
    except Exception as e:
        print(f"❌ Error durante la optimización: {e}")

    print("--- Mantenimiento Completado ---")

if __name__ == "__main__":
    maintenance()
