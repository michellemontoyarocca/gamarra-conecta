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
| `/mi-negocio` | Alta y edición del perfil; devuelve el estado a pendiente | Autenticado |
| `/orientacion` | Envío y consulta de solicitudes propias | Autenticado |
| `/admin` | Indicadores y pendientes | Administrador |
| `/admin/negocios/<id>/publicar` | Moderación de perfil | Administrador |
| `/admin/solicitudes/<id>/revisar` | Cambio de estado de solicitud | Administrador |

## Seguridad incorporada

Las contraseñas se almacenan como hashes generados por Werkzeug. Todas las operaciones POST exigen token CSRF. Las consultas SQL usan parámetros. Las rutas protegidas comprueban sesión y rol. La cookie de sesión tiene HttpOnly y SameSite=Lax; al definir `GAMARRA_ENV=production`, también exige Secure. En producción debe definirse además `GAMARRA_SECRET_KEY` con un valor aleatorio persistente y servirse solo por HTTPS. Los datos que introduce el usuario se escapan mediante Jinja; no se usa HTML sin filtrar.

La aplicación usa SQLite para una demostración académica de escala pequeña. Para un despliegue concurrente o de mayor escala conviene migrar a PostgreSQL y evaluar copias de seguridad, monitoreo, recuperación y gestión de datos personales.

## Verificación local

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py tests
python -m pip install bandit pip-audit
bandit -r app.py -ll
pip-audit -r requirements.txt
```

GitHub Actions ejecuta las mismas fases de compilación, pruebas, análisis estático de seguridad y auditoría de dependencias en cada push y pull request. El job `deploy` queda omitido hasta configurar la variable `DEPLOY_ENABLED=true`, el entorno `production` y los secretos `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`, `DEPLOY_HOST` y `DEPLOY_USER` en el repositorio. Un archivo de workflow por sí solo no demuestra una ejecución remota exitosa: esa evidencia debe obtenerse en la pestaña Actions del repositorio publicado.

## Ramas y trazabilidad

Propuesta de flujo: `test` para integración, ramas `feature/hu-XX` para cada historia, pull requests revisados hacia `main`; `main` contiene el código estable. Referenciar la clave real de Jira en el título de cada PR y en los commits. Las claves, PR y capturas se agregan al informe una vez existan.

## Despliegue

En un VPS: clonar el repositorio en `/srv/gamarra-conecta`, instalar Python y dependencias, establecer `GAMARRA_ENV=production` y `GAMARRA_SECRET_KEY`, ejecutar Flask mediante Gunicorn detrás de Nginx con HTTPS y restringir acceso al archivo SQLite. El usuario remoto del pipeline debe poder reiniciar únicamente el servicio `gamarra-conecta` sin contraseña, con una regla de `sudoers` específica; no otorgar privilegios generales. Antes de publicar, agregar respaldo de `instance/`, configuración de dominio, servicio del sistema y pruebas de humo. Este repositorio local no acredita un despliegue público.
