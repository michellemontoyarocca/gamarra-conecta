# Validación del despliegue automático

Este commit activa una ejecución completa de GitHub Actions sobre `main` después de configurar los secretos de despliegue. La ejecución debe superar compilación, 54 pruebas, Bandit, pip-audit y detect-secrets, conservar los reportes como artefacto, desplegar en el VPS y comprobar `/salud`. El resultado verificable se documenta en el informe de la práctica.
