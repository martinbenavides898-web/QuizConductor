# Conduce+ v0.3 — Streamlit + Supabase

Aplicación mobile-first para preparar la Licencia de Conducir Clase B en Chile mediante preguntas situacionales, retroalimentación pedagógica y refuerzo adaptativo.

## Correcciones de la versión 0.3

- Calendario mensual real, alineado de lunes a domingo y con navegación entre meses.
- Distinción entre desafío completado, desafío iniciado y práctica registrada.
- Gráfico de evolución reconstruido con precisión diaria y precisión acumulada.
- El gráfico funciona incluso con un solo día de actividad y conserva correctamente las fechas de Chile.
- Alternativas mezcladas de forma estable, pero siempre presentadas ordenadamente como A, B, C y D.
- La corrección mantiene exactamente el mismo orden de alternativas mostrado en la pregunta.
- Botón final corregido: después de la décima pregunta lleva a resultados.
- Conteos y barras de progreso calculados desde la sesión real, sin valores fijos.
- Perfil único automático, sin pantalla de usuario ni contraseña.
- Migración compatible: si ya había progreso en Supabase, reutiliza el perfil existente.
- Logo y favicon C+.
- Referencias editoriales corregidas para las preguntas Q039 y Q040.
- Validaciones y pruebas automatizadas ampliadas.

## Funciones principales

- Desafío diario de 10 preguntas: 3 fáciles, 4 medias y 3 difíciles.
- Prácticas adicionales ilimitadas.
- Banco inicial de 42 preguntas trazables al **Libro para la Conducción en Chile, CONASET 2024**.
- Explicación, consejo práctico y referencia oficial después de cada respuesta.
- Selección adaptativa según historial, debilidades y repetición.
- Precisión general y por tema, evolución, calendario, racha, XP y logros.
- Persistencia remota en Supabase/PostgreSQL.

## Actualizar una instalación existente

1. Reemplaza en GitHub todos los archivos por los de esta versión.
2. Conserva los mismos Secrets de Streamlit.
3. No necesitas volver a ejecutar `supabase/schema.sql` si las tablas ya existen.
4. Streamlit debería reconstruir la app automáticamente.

## Instalación desde cero

### 1. Crear el proyecto Supabase

Crea un proyecto y espera a que quede activo.

### 2. Crear las tablas

En **SQL Editor → New query**, copia todo el contenido de:

```text
supabase/schema.sql
```

Luego presiona **Run**.

### 3. Configurar Streamlit Cloud

En **App settings → Secrets**, pega:

```toml
[supabase]
url = "https://TU-PROYECTO.supabase.co"
secret_key = "sb_secret_REEMPLAZAR"
```

Nunca subas la Secret key a GitHub.

### 4. Desplegar

Sube el proyecto a la raíz del repositorio y utiliza:

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
streamlit run streamlit_app.py
```

## Seguridad y alcance

La Secret key se utiliza únicamente en el backend de Streamlit. Las tablas tienen Row Level Security y no ofrecen acceso público directo. Esta configuración está pensada para el uso privado de una sola persona.

Supabase reduce el riesgo de pérdida de progreso frente a reinicios de Streamlit, pero ningún servicio garantiza disponibilidad absoluta. Para información importante, conviene mantener respaldos del proyecto.

## Fuente oficial

El contenido se construyó exclusivamente a partir de:

```text
docs/Libro_oficial_CONASET_Clase_B_2024.pdf
```

La aplicación entrena comprensión del material oficial y toma de decisiones seguras; no afirma reproducir preguntas exactas del examen municipal.
