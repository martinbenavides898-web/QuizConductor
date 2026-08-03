# Configuración de Supabase — guía directa

## A. Crear base de datos

1. Entra a Supabase y crea un proyecto.
2. Abre **SQL Editor**.
3. Presiona **New query**.
4. Abre en este repositorio `supabase/schema.sql`.
5. Copia todo, pégalo en el editor y presiona **Run**.
6. En **Table Editor** deben aparecer:
   - `profiles`
   - `quiz_sessions`
   - `attempts`

## B. Copiar las credenciales correctas

1. Abre **Project Settings → API Keys**.
2. Copia la **Project URL**.
3. Copia una **Secret key** de servidor (`sb_secret_...`).
4. No uses la `publishable key`.

## C. Guardarlas en Streamlit

1. En Streamlit Community Cloud abre la app.
2. Entra a **App settings → Secrets**.
3. Pega:

```toml
[supabase]
url = "https://TU-PROYECTO.supabase.co"
secret_key = "sb_secret_REEMPLAZAR"
```

4. Guarda y reinicia.

## D. Prueba mínima

1. Abre la app.
2. Crea un perfil.
3. Responde una pregunta.
4. Cierra sesión.
5. Vuelve a entrar desde otro navegador con el mismo usuario y clave.
6. La respuesta y el avance deben seguir disponibles.

## Errores típicos

### “Faltan las credenciales”
Los secretos no fueron guardados o el bloque TOML está mal escrito.

### “Se configuró una publishable key”
Copiaste la clave pública. Debes usar una Secret key de servidor.

### “Faltan las tablas”
No ejecutaste `supabase/schema.sql`, o lo ejecutaste en otro proyecto.

### La app no conecta después de guardar Secrets
Reinicia la aplicación desde Streamlit Cloud. Verifica que la URL corresponda al mismo proyecto que la Secret key.

### No aparece el progreso
Confirma que ingresaste exactamente al mismo perfil. Los nombres no distinguen mayúsculas ni tildes, pero sí palabras diferentes.
