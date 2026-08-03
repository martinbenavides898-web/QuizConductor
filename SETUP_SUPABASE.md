# Configuración de Supabase

## Instalación nueva

1. Crea un proyecto en Supabase.
2. Abre **SQL Editor → New query**.
3. Copia todo el archivo `supabase/schema.sql` y presiona **Run**.
4. En **Project Settings → API Keys**, copia la Project URL y una Secret key de servidor.
5. En Streamlit Community Cloud abre **App settings → Secrets** y pega:

```toml
[supabase]
url = "https://TU-PROYECTO.supabase.co"
secret_key = "sb_secret_REEMPLAZAR"
```

6. Reinicia la app.

La aplicación crea o reutiliza automáticamente un único perfil interno. No hay registro, inicio de sesión ni contraseña visible.

## Actualización desde una versión anterior

- Reemplaza los archivos del repositorio.
- Mantén los mismos Secrets.
- No borres las tablas.
- No vuelvas a ejecutar el esquema salvo que estés creando un proyecto nuevo.
- La versión 0.3 prioriza el perfil interno existente y conserva su historial.

## Prueba mínima

1. Abre la aplicación.
2. Responde una pregunta.
3. Cierra la pestaña.
4. Abre nuevamente el enlace.
5. La sesión debe continuar desde el mismo punto.

## Errores frecuentes

### Faltan las credenciales
Revisa el bloque `[supabase]` en los Secrets de Streamlit.

### Se configuró una publishable key
La app necesita una Secret key de servidor.

### Faltan las tablas
Ejecuta `supabase/schema.sql` en el mismo proyecto al que apuntan los Secrets.

### El progreso no aparece
Confirma que la URL y la Secret key correspondan al mismo proyecto de Supabase usado anteriormente.
