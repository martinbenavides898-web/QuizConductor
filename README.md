# Conduce+ — MVP Streamlit

Plataforma móvil de aprendizaje para preparar la Licencia de Conducir Clase B en Chile mediante preguntas situacionales, retroalimentación pedagógica y adaptación básica por temas débiles.

## Qué incluye

- Diseño mobile-first optimizado para iPhone.
- Desafío diario de 10 preguntas: 3 fáciles, 4 medias y 3 difíciles.
- Prácticas nuevas ilimitadas.
- Banco inicial de 42 preguntas trazables al **Libro para la Conducción en Chile, CONASET 2024**.
- Explicación, consejo práctico y referencia de página después de cada respuesta.
- Algoritmo adaptativo que aumenta el peso de los temas con menor precisión.
- Precisión general y por tema, evolución, racha, XP y logros.
- Guardado automático en SQLite.

## Subir a GitHub

1. Crea un repositorio nuevo en GitHub.
2. Sube **todo el contenido de esta carpeta** a la raíz del repositorio.
3. Confirma que `streamlit_app.py` y `requirements.txt` queden visibles en la raíz.

## Publicar en Streamlit Community Cloud

1. Entra a Streamlit Community Cloud.
2. Pulsa **Create app**.
3. Selecciona tu repositorio y la rama `main`.
4. En **Main file path**, usa:

```text
streamlit_app.py
```

5. Pulsa **Deploy**.

No requiere secrets ni configuración adicional para iniciar.

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

## Importante sobre persistencia

El MVP usa SQLite para funcionar de inmediato. En Streamlit Community Cloud, los datos escritos en disco pueden perderse cuando la aplicación se reinicia o vuelve a desplegarse. Para uso público o persistencia garantizada, la siguiente versión debe conectar los repositorios a Supabase/PostgreSQL.

## Fuente de contenido

El contenido se construyó exclusivamente a partir del archivo incluido en:

```text
docs/Libro_oficial_CONASET_Clase_B_2024.pdf
```

Cada pregunta contiene documento, capítulo, sección y página. Este MVP entrena comprensión del material oficial; no afirma reproducir las preguntas exactas del examen municipal.

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
tests/
  test_questions.py
.streamlit/
  config.toml
```
