# Conduce+ v0.2 — Streamlit + Supabase

Plataforma mobile-first para preparar la Licencia de Conducir Clase B en Chile mediante preguntas situacionales, retroalimentación pedagógica y adaptación básica por temas débiles.

## Qué cambia en esta versión

- Persistencia remota en **Supabase/PostgreSQL**.
- El progreso no depende del disco temporal de Streamlit Cloud.
- Perfiles protegidos con nombre de usuario y clave numérica de 6 dígitos.
- Las claves se almacenan con PBKDF2-SHA256 y salt aleatorio; nunca en texto legible.
- Una única sesión diaria por perfil y fecha, incluso si se abren varias pestañas.
- Respuestas idempotentes: un doble toque no duplica registros.
- Reintentos automáticos ante fallas transitorias de red.
- Restricciones y claves foráneas para proteger la integridad de los datos.
- Pantalla de diagnóstico cuando faltan secretos, tablas o conexión.

## Contenido actual

- Diseño optimizado para iPhone y compatible con computador.
- Desafío diario de 10 preguntas: 3 fáciles, 4 medias y 3 difíciles.
- Prácticas nuevas ilimitadas.
- Banco inicial de 42 preguntas trazables al **Libro para la Conducción en Chile, CONASET 2024**.
- Explicación, consejo práctico y referencia de página después de cada respuesta.
- Algoritmo adaptativo según temas débiles.
- Precisión general y por tema, evolución, racha, XP y logros.

## Instalación rápida

### 1. Crear el proyecto Supabase

Crea un proyecto en Supabase y espera a que quede activo.

### 2. Crear las tablas

En Supabase abre **SQL Editor → New query**, copia todo el archivo:

```text
supabase/schema.sql
```

y presiona **Run**.

### 3. Obtener las credenciales

En Supabase abre **Project Settings → API Keys** y copia:

- Project URL.
- Una **Secret key** de servidor, normalmente comienza con `sb_secret_`.

También funciona temporalmente la clave heredada `service_role`, pero se recomienda la nueva Secret key.

### 4. Configurar Streamlit Cloud

En la aplicación desplegada abre:

```text
App settings → Secrets
```

Pega:

```toml
[supabase]
url = "https://TU-PROYECTO.supabase.co"
secret_key = "sb_secret_REEMPLAZAR"
```

Guarda los cambios y reinicia la app.

> Nunca subas la Secret key a GitHub. El repositorio ya ignora `.streamlit/secrets.toml`.

### 5. Subir a GitHub y desplegar

Sube todo el contenido de esta carpeta a la raíz del repositorio. En Streamlit Community Cloud usa:

```text
streamlit_app.py
```

como **Main file path**.

## Ejecutar localmente

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copia el ejemplo de secretos:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Completa la URL y la Secret key, luego ejecuta:

```bash
streamlit run streamlit_app.py
```

## Seguridad

La aplicación usa la Secret key únicamente en el backend Python de Streamlit. Las tablas tienen Row Level Security habilitado y no poseen políticas públicas para `anon` ni `authenticated`.

Este sistema es adecuado para el MVP familiar. Antes de una apertura masiva conviene migrar el ingreso a Supabase Auth con correo, recuperación de contraseña, rate limiting y auditoría.

## Respaldo

Supabase evita que el progreso desaparezca al reiniciarse Streamlit, pero ningún servicio puede prometer disponibilidad absoluta. Para datos importantes, activa respaldos en Supabase según el plan utilizado y exporta periódicamente las tablas.

## Estructura

```text
streamlit_app.py
app/
  config.py
  data.py
  database.py
  engine.py
  ui.py
data/
  questions.json
docs/
  Libro_oficial_CONASET_Clase_B_2024.pdf
supabase/
  schema.sql
.streamlit/
  config.toml
  secrets.toml.example
tests/
```

## Fuente oficial

El contenido se construyó exclusivamente a partir del documento incluido en:

```text
docs/Libro_oficial_CONASET_Clase_B_2024.pdf
```

Cada pregunta contiene documento, capítulo, sección y página. La aplicación entrena comprensión del material oficial; no afirma reproducir las preguntas exactas del examen municipal.
