# PetCare | EVA 3 Desarrollo Backend

**Benjamín Seguel Cerda · INACAP Temuco · Proyecto 1**

PetCare centraliza la agenda veterinaria, los datos de tutores y mascotas, las fichas clínicas y el seguimiento de vacunas y controles periódicos.

## Estado del despliegue

**Aplicación desplegada:** [http://54.92.176.223/](http://54.92.176.223/)  
**Django Admin:** [http://54.92.176.223/admin/](http://54.92.176.223/admin/)

Verificado el 11 de noviembre de 2026 en AWS Academy, región `us-east-1`, instancia EC2 `sandias-pana-walter` con Ubuntu 22.04. Nginx, Gunicorn y PostgreSQL están activos y la migración de la clínica está aplicada. La página de inicio de sesión se abrió desde un navegador externo. Para la defensa, el Learner Lab y la instancia deben estar en ejecución.

## Funciones

- **Tutores y mascotas.** Alta, consulta, edición y eliminación. Se protege la eliminación de datos con registros dependientes.
- **Agenda.** Consulta por fecha y horarios semanales por profesional. Las citas deben quedar dentro del horario y no solaparse. Cancelar una cita libera el bloque.
- **Fichas clínicas.** Cada cita puede tener una ficha con diagnóstico, tratamiento, receta y exámenes.
- **Recordatorios.** Vacunas y controles se muestran en el panel. Al completar un recordatorio con intervalo, se programa el siguiente a partir de su fecha. El aviso aparece dentro de la aplicación.
- **Acceso.** Django autentica mediante sesiones y valida CSRF en los cambios. Los permisos de Django se aplican en web, API y Admin. Recepción no ve fichas clínicas. Los profesionales pueden gestionarlas. El administrador gestiona cuentas y permisos.

## Ejecución local

Se requiere Python 3.10 o posterior y, para usar la configuración principal, PostgreSQL. Crea primero la base y el rol local `petcare` y asigna el rol como propietario. Luego:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export DJANGO_DEBUG=1
export POSTGRES_DB=petcare POSTGRES_USER=petcare POSTGRES_HOST=127.0.0.1
read -rsp 'Contraseña del rol de PostgreSQL: ' POSTGRES_PASSWORD
export POSTGRES_PASSWORD
printf '\n'
python manage.py migrate
python manage.py preparar_roles
python manage.py createsuperuser
python manage.py cargar_demo
python manage.py runserver
```

Para revisar la aplicación sin instalar PostgreSQL localmente, usa `export PETCARE_DEV_SQLITE=1` antes de migrar. Esa opción funciona solo en modo de desarrollo. En una base de pruebas PostgreSQL, `python manage.py test` necesita que el rol pueda crear la base temporal de pruebas. La cuenta de producción de EC2 solo requiere acceso a su propia base.

| Ruta | Uso |
| --- | --- |
| `/` | Agenda, horarios y recordatorios |
| `/registros/tutores/` | Gestión de tutores |
| `/registros/mascotas/` | Gestión de mascotas |
| `/api/` | API REST navegable. Iniciar sesión para consultar recursos |
| `/admin/` | Administración. Requiere una cuenta con acceso de personal |

Los demás recursos de la API se encuentran en `/api/profesionales/`, `/api/horarios/`, `/api/citas/`, `/api/fichas/` y `/api/recordatorios/`. Los permisos de lectura, creación, modificación y eliminación se comprueban por modelo.

## Despliegue en una EC2 Ubuntu 22.04

Nginx recibe las solicitudes públicas. Gunicorn escucha en `127.0.0.1:8011` y Django se conecta a PostgreSQL en la misma instancia. PostgreSQL y Gunicorn no requieren puertos públicos. La instalación genera la clave de Django y la contraseña de PostgreSQL en `/etc/petcare.env`.

1. Inicia AWS Academy Learner Lab y comprueba que EC2 esté en ejecución. El grupo de seguridad debe admitir TCP 80 público y SSH desde tu IP.
2. Copia este código a la instancia. Dentro de la carpeta del proyecto, ejecuta:

   ```bash
   sudo bash deploy/install.sh IP_PUBLICA_ACTUAL
   sudo bash deploy/manage.sh createsuperuser
   sudo bash deploy/manage.sh cargar_demo
   ```

3. Desde otro equipo o navegador, verifica `http://IP_PUBLICA_ACTUAL/`, `/admin/` y el inicio de sesión. Usa datos ficticios para la demostración. Si se dispone de un dominio y TLS en Nginx, se puede activar `DJANGO_HTTPS=1` en el archivo de entorno y reiniciar `petcare`.
4. Comprueba el motor y las migraciones dentro de EC2:

   ```bash
   sudo bash deploy/manage.sh shell -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor)"
   sudo bash deploy/manage.sh showmigrations clinic
   sudo systemctl is-active petcare postgresql nginx
   ```

El nombre de servidor en Nginx es la IP o DNS ingresado. En la instancia de la receta, la configuración antigua continúa disponible como sitio por defecto, mientras PetCare responde a solicitudes dirigidas a ese nombre exacto.

## Demostración

1. Inicia sesión. Abre la agenda del día con `cargar_demo` y revisa el horario de la profesional.
2. Registra un tutor y su mascota. Agenda una cita y prueba intentar otra en el mismo bloque para ver la validación.
3. Registra la ficha con diagnóstico, tratamiento, receta y exámenes. Abre el Admin y filtra citas por profesional.
4. Marca como completado el recordatorio de vacuna y comprueba que se crea la próxima fecha.
5. Muestra la API con la sesión abierta. Una cuenta de Recepción puede ver mascotas, pero recibe 403 en fichas clínicas.

## Verificación

`python manage.py check` y `python manage.py makemigrations --check --dry-run` finalizaron correctamente. La suite pasó 12 pruebas con SQLite de desarrollo y las mismas 12 con PostgreSQL en EC2. Las pruebas cubren CRUD, permisos, protección CSRF, agenda, fichas, recurrencia y renderizado del Admin.
