# Propuesta de Rediseño Frontend: Proyecto "Pixel Wonder"

## 1. Concepto Visual
El rediseño del frontend adoptará una estética **Pixel Art (8-bit / 16-bit)**, evocando la nostalgia de los videojuegos retro y las interfaces de computadora de los años 80/90. Este estilo visual no solo es distintivo, sino que refuerza el carácter lúdico y de "exploración" de la plataforma iWonder.

### Estilo: "Retro-Futurismo Lúdico"
-   Interfaz basada en bloques y bordes gruesos.
-   Elementos de UI que recuerdan a cajas de diálogo de RPGs clásicos.
-   Animaciones "frame-by-frame" simples pero encantadoras.

---

## 2. Paleta de Colores
Se utilizará una paleta de alto contraste optimizada para el estilo pixel art, con un modo oscuro por defecto para resaltar los colores "neón" y pasteles.

| Uso | Color HEX | Descripción |
|-----|-----------|-------------|
| **Fondo Principal** | `#212529` | Gris oscuro casi negro (tipo terminal). |
| **Fondo Secundario**| `#343A40` | Gris para contenedores/cartas. |
| **Acento Primario** | `#9D4EDD` | Violeta eléctrico (Botones principales, acciones). |
| **Acento Secundario**| `#00B4D8` | Cyan retro (Links, info). |
| **Éxito** | `#70E000` | Verde lima brillante. |
| **Alerta/Error** | `#EF233C` | Rojo arcade. |
| **Texto Principal** | `#F8F9FA` | Blanco roto (mejor legibilidad). |
| **Bordes** | `#000000` | Negro puro, grosor 2px-4px sólido. |

---

## 3. Tipografía
La tipografía es crucial para vender el efecto pixelado sin sacrificar la legibilidad.

*   **Títulos y Encabezados**: **"Press Start 2P"** (Google Fonts). Fuente bitmap gruesa, ideal para logos y headers.
*   **Cuerpo de Texto**: **"VT323"** o **"Courier Prime"**. Fuentes monoespaciadas que simulan terminales o juegos de texto, pero legibles en tamaños pequeños.

---

## 4. Componentes UI (Design System)

### 4.1 Botones (NES Style)
Los botones tendrán un aspecto tridimensional mediante sombras sólidas CSS.
```css
.btn-pixel {
  border: 4px solid #000;
  box-shadow: 4px 4px 0px #000;
  background-color: #9D4EDD;
  color: #fff;
  font-family: 'Press Start 2P', cursive;
  transition: transform 0.1s;
}
.btn-pixel:active {
  transform: translate(4px, 4px);
  box-shadow: 0px 0px 0px #000;
}
```

### 4.2 Avatares
Se implementará un generador de avatares pixelados (o integración con servicios como DiceBear Pixel Art). Cada usuario tendrá un avatar único generado basado en su hash de username.

### 4.3 Cajas de Diálogo (Feed Cards)
Las preguntas y respuestas se presentarán como "burbujas de diálogo" de RPG.
-   **Pregunta**: Fondo oscuro con borde blanco discontinuo.
-   **Respuesta**: Fondo claro (o color de acento suave) con borde sólido.

### 4.4 Animaciones
-   **Loading**: Un icono de "reloj de arena" o un personaje caminando en 2 frames.
-   **Interacciones**: Efecto "bounce" al hacer hover en elementos interactivos.
-   **Transiciones**: Efecto "Wipe" (barrido) pixelado al cambiar de página.

---

## 5. Implementación Técnica Sugerida

### 5.1 Framework CSS
Se recomienda utilizar **NES.css** (https://nostalgic-css.github.io/NES.css/), un framework CSS que provee componentes estilo NES (Nintendo Entertainment System) listos para usar. Esto acelerará el desarrollo significativamente.

### 5.2 Stack Frontend
-   **React.js** o **Vue.js**: Para el manejo de estado y componentes.
-   **Axios**: Para consumo de la API REST de iWonder.
-   **Socket.io-client**: Para las notificaciones en tiempo real.

### 5.3 Mockup de Layout (Home)
```
+-------------------------------------------------------+
|  [LOGO: iWonder] (8-bit)        [Avatar] [Logout]     |
+-------------------------------------------------------+
|                                                       |
|  +-------------------+    +------------------------+  |
|  | MENU              |    | FEED DE CURIOSIDAD     |  |
|  | > Inicio          |    |                        |  |
|  |   Explorar        |    | +--------------------+ |  |
|  |   Perfil          |    | | [Avatar] UserA     | |  |
|  |   Configuración   |    | | Q: ¿Cuál es tu...  | |  |
|  +-------------------+    | | ------------------ | |  |
|                           | | A: Mi juego fav... | |  |
|                           | +--------------------+ |  |
|                           |                        |  |
|                           | +--------------------+ |  |
|                           | | [Avatar] UserB     | |  |
|                           | | ...                | |  |
|                           | +--------------------+ |  |
|                           +------------------------+  |
|                                                       |
+-------------------------------------------------------+
```
