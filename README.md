# Gamarra Conecta

MVP académico para la Práctica Calificada 2 de Proyecto Final de Carrera III. Permite que comerciantes registren un negocio, que visitantes busquen perfiles publicados y que comerciantes registren solicitudes de orientación sobre formalización. El administrador modera perfiles y marca solicitudes revisadas. El sistema no verifica licencias, no procesa pagos y no emite asesoría legal o tributaria.

## Requisitos y ejecución

Python 3.10 o superior. Desde esta carpeta:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000`. La base SQLite se crea en `instance/gamarra.sqlite3` y queda fuera de Git. Para crear un administrador, detener el servidor y ejecutar:

```powershell
python -m flask --app app create-admin admin@ejemplo.com --name "Michelle Montoya"
```

El comando solicita una contraseña de al menos 10 caracteres sin mostrarla. No se incluye ningún administrador ni contraseña predeterminada.

## Rutas

| Ruta | Función | Acceso |
| --- | --- | --- |
| `/` | Portada | Público |
| `/registro`, `/login` | Cuenta de comerciante | Público |
| `/negocios` | Directorio, búsqueda y filtro de rubro | Público |
| `/negocios/<id>` | Ficha pública de un negocio publicado | Público |
| `/guia` | Guía de formalización con enlaces oficiales | Público |
| `/salud` | Prueba de humo: devuelve `{"estado":"ok"}` | Público |
| `/mi-negocio` | Alta y edición del perfil; devuelve el estado a pendiente | Autenticado |
| `/orientacion` | Envío y consulta de solicitudes propias y su estado | Autenticado |
| `/admin` | Indicadores y pendientes | Administrador |
| `/admin/negocios/<id>/publicar` | Aprobar un perfil | Administrador |
| `/admin/negocios/<id>/rechazar` | Rechazar un perfil | Administrador |
| `/admin/solicitudes/<id>/revisar` | Cambio de estado de solicitud | Administrador |

## Seguridad incorporada

Las contraseñas se almacenan como hashes generados por Werkzeug. Todas las operaciones POST exigen token CSRF. Las consultas SQL usan parámetros. Las rutas protegidas comprueban sesión y rol. La cookie de sesión tiene HttpOnly y SameSite=Lax; al definir `GAMARRA_ENV=production`, también exige Secure. En producción debe definirse además `GAMARRA_SECRET_KEY` con un valor aleatorio persistente y servirse solo por HTTPS. Los datos que introduce el usuario se escapan mediante Jinja; no se usa HTML sin filtrar.

El ingreso limita a cinco intentos fallidos por correo durante quince minutos, con el contador compartido en SQLite entre los procesos Gunicorn. La prueba que detectó y verificó la corrección del problema está documentada en `docs/hallazgo_seguridad.md`.

La aplicación usa SQLite para una demostración académica de escala pequeña. Para un despliegue concurrente o de mayor escala conviene migrar a PostgreSQL y evaluar copias de seguridad, monitoreo, recuperación y gestión de datos personales.

## Verificación local

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py tests
python -m pip install bandit pip-audit detect-secrets==1.5.0
python -m bandit -r app.py -ll
python -m pip_audit -r requirements.txt
detect-secrets scan --all-files
```

GitHub Actions ejecuta compilación, 54 pruebas, Bandit, pip-audit y detect-secrets en cada push y pull request, y conserva los tres reportes de seguridad como artefacto. Un push a `main` que supera `calidad` inicia `deploy` cuando `DEPLOY_ENABLED=true`. La clave SSH del job está limitada en el VPS a ejecutar `scripts/deploy.sh`: actualiza `main`, instala dependencias en el entorno virtual del servidor, reinicia el servicio y comprueba `/salud`. Antes de desplegar guarda una copia de SQLite; si falla la instalación, el reinicio o la comprobación de salud, restaura el commit anterior. El job necesita el entorno `production` y los secretos `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`, `DEPLOY_HOST` y `DEPLOY_USER`.

## Ramas y trazabilidad

`main` es la rama de producción y `test` la de integración. Cada historia de Jira (espacio GC) se trabajó en una rama `feature/GC-n-...` desde `test`; el commit lleva como mensaje la clave y el nombre exacto de la historia, se integra en `test` con un merge sin fast-forward y el Pull Request #1 integró `test` en `main`. Cada push ejecuta el workflow «CI, seguridad y despliegue».

## Despliegue

La aplicación está publicada en https://gamarra.comextech.es sobre un VPS Ubuntu: carpeta `/srv/gamarra-conecta`, usuario del sistema `gamarra` sin privilegios, entorno virtual en `/srv/gamarra-conecta-home/venv`, servicio `systemd` `gamarra-conecta` (Gunicorn en `127.0.0.1:8018`), Nginx con certificado de Let's Encrypt y redirección de HTTP a HTTPS. `GAMARRA_ENV=production` y `GAMARRA_SECRET_KEY` están en `/etc/gamarra-conecta.env` (permisos 600, fuera de Git). Una regla de `sudoers` permite al usuario `gamarra` reiniciar únicamente ese servicio. Un respaldo diario a las 03:30 copia `instance/gamarra.sqlite3` a `/srv/gamarra-backups` y conserva 14 días. El procedimiento reproducible está en `scripts/deploy.sh` y el resultado de cada ejecución se comprueba en GitHub Actions y en `/salud`.
