# Hallazgo corregido: intentos ilimitados de ingreso

## Detección

La revisión del flujo de autenticación encontró que `/login` permitía repetir contraseñas incorrectas sin límite. Se añadió `test_login_blocks_brute_force_and_recovers_after_window` como prueba de seguridad automatizada. Al ejecutarla contra el código anterior al cambio, falló: el sexto intento con la contraseña correcta ingresó (HTTP 200) cuando debía bloquearse (HTTP 429). La salida de esa ejecución se conserva en la evidencia del informe.

## Corrección

La aplicación guarda en SQLite los fallos por correo normalizado. Tras cinco fallos dentro de quince minutos, rechaza los siguientes intentos con HTTP 429. Al terminar la ventana se puede volver a ingresar y un ingreso correcto limpia el contador. SQLite permite aplicar el control a los dos procesos Gunicorn del VPS; los datos persisten al reiniciar el servicio.

La prueba de seguridad pasó después de la corrección. Las 54 pruebas de la aplicación, Bandit, pip-audit y detect-secrets forman las puertas de calidad del pipeline. El escaneo de secretos identificó inicialmente cadenas de prueba en `tests/`, que se revisaron y marcaron explícitamente como datos ficticios; el resultado final quedó en cero hallazgos.

## Reproducción

```bash
python -m unittest discover -s tests -p test_app.py -k test_login_blocks
python -m unittest discover -s tests -v
bandit -r app.py -ll
pip-audit -r requirements.txt
detect-secrets scan --all-files
```

El control limita intentos por cuenta. Una futura versión podría añadir límites por origen y alertas de actividad anómala.
