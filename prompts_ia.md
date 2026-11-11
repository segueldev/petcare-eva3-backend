# Registro de apoyo de IA

**Herramienta:** ChatGPT / Codex  
**Evaluación:** EVA 3 Desarrollo Backend  
**Caso asignado:** 1, PetCare

## Solicitud y material de partida

Benjamín pidió preparar la entrega de Backend a partir de las dos carpetas locales, que incluían la pauta EVA 3, la planilla de asignación de casos y una receta anterior de AWS. El asistente revisó la pauta y la planilla, donde figura el tema 1. Usó la receta anterior como referencia de infraestructura.

## Apoyos solicitados para preparar la entrega

- Identificar el caso asignado y los requisitos de entrega. El apoyo determinó que el proyecto era PetCare y que el aula esperaba el enlace al repositorio.
- Preparar el código Django/DRF del caso. El apoyo generó modelos, migración, vistas web, API y panel Admin. El proyecto comprueba horarios, rechaza citas superpuestas y programa recordatorios recurrentes.
- Reutilizar la arquitectura de AWS de la receta. El apoyo generó la configuración de Gunicorn, Nginx y PostgreSQL y las instrucciones para instalar en EC2.
- Validar el funcionamiento antes de preparar el paquete. El apoyo ejecutó los chequeos de Django y 12 pruebas con SQLite de desarrollo. Luego se instalaron los servicios en la EC2 existente, se ejecutaron las mismas 12 pruebas con PostgreSQL y se comprobó la página pública de inicio de sesión.

- Preparar la defensa en el PC. El apoyo añadió un comando de arranque local, explicó la relación con el ejercicio Sandías Pana Walter y comentó las validaciones de agenda, los permisos, la recurrencia y el despliegue.
