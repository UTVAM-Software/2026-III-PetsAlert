# Pets Alert

Aplicación web (PWA) para reportar y encontrar mascotas perdidas. Proyecto Django con PostgreSQL.

La aplicación ya no depende de Firebase: usuarios, reportes, fotos, chat y perfil viven en
Django y PostgreSQL.

## Requisitos

- Python 3.12 o superior
- PostgreSQL 15 o superior (con pgAdmin o psql)

## Puesta en marcha (Windows, PowerShell)

1. Crea en PostgreSQL un usuario y una base de datos (por ejemplo `petsalert` / `petsalert`). Desde pgAdmin:
   *Login/Group Roles → Create* y *Databases → Create → Database* (con ese usuario como dueño).
2. Entorno virtual y dependencias:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configuración: copia `.env.example` a `.env` y completa los datos de tu base
   (nombre, usuario, contraseña y **puerto**: revisa el tuyo en pgAdmin, puede ser 5432 o 5433).
4. Tablas y datos base (crea también los grupos y permisos iniciales):
   ```powershell
   python manage.py migrate
   ```
5. Usuario administrador (opcional, para entrar a `/admin/`):
   ```powershell
   python manage.py createsuperuser
   ```
6. Servidor:
   ```powershell
   python manage.py runserver
   ```
   Abre http://127.0.0.1:8000/

Si cambias de rama o alguien actualiza los modelos, vuelve a correr `python manage.py migrate`.

## Correos en desarrollo

Si `EMAIL_HOST` está vacío en el `.env`, los correos no se envían: se **imprimen en la terminal** donde corre
`runserver`. Ahí aparece el enlace para verificar tu cuenta al registrarte y el de recuperar contraseña.

## Pruebas

```powershell
python manage.py test
```

Django crea una base temporal (`test_<nombre>`), así que el usuario de PostgreSQL necesita el permiso `CREATEDB`
(en pgAdmin: *Login/Group Roles → tu usuario → Privileges → Can create databases?*).

## Estructura

| Carpeta | Contenido |
|---|---|
| `pets_amber_web/` | Configuración del proyecto (`settings.py`, `urls.py`) |
| `auth_app/` | Usuario propio con grupos y permisos nativos, registro, login, verificación de correo y recuperación de contraseña |
| `feed/` | Reportes de mascotas (modelo, API en `/feed/api/reports/` y pantallas) |
| `chat/` | Chats por reporte y mensajes (modelos, API en `/chat/api/chats/` y pantallas) |
| `profiles/` | Pantallas de perfil, privacidad y "Mis reportes", y la API `/profile/api/me/` (los datos del perfil están en `auth_app.Usuario`) |
| `panel/` | Panel `/panel/` con CRUD de usuarios, grupos, permisos, reportes, chats y mensajes |
| `templates/`, `static/` | Plantilla base y estilos |
| `Documentacion/` | Diagramas de la base de datos |

## Usuarios, grupos y permisos

- El modelo de usuario es `auth_app.Usuario` (inicia sesión con el correo) y usa el sistema nativo de Django:
  `groups`, `user_permissions`, `has_perm` y `PermissionsMixin`.
- Los grupos base están en `auth_app/catalogo.py` y se crean solos después de cada `migrate`:
  **Usuario básico** (crea, edita y elimina sus reportes y usa el chat), **Moderador** (además modera cualquier reporte con
  `feed.moderar_reportes`) y **Administrador** (siempre recibe todos los permisos, incluido `auth_app.acceder_panel`).
  Todo usuario nuevo entra al grupo Usuario básico; `createsuperuser` lo deja en Administrador.
- Permisos propios de la aplicación: `auth_app.acceder_panel`, `feed.moderar_reportes` y `chat.usar_chat`.
  El resto son los permisos nativos de cada modelo (`feed.add_petreport`, `auth.view_group`, etc.).
- Todas las pantallas exigen sesión iniciada; las que requieren un permiso lo declaran con `@login_required` y
  `@permission_required(...)` (o `permission_required` en las vistas basadas en clases).

## Panel de administración (`/panel/`)

CRUD y listado de usuarios, grupos, permisos, reportes, chats y mensajes, sin depender de `/admin/`. Cada vista exige
`auth_app.acceder_panel` y el permiso nativo del modelo (`view`, `add`, `change` o `delete`), así que solo el grupo
Administrador (o grupos que el administrador cree con esos permisos) puede usarlo. Un usuario sin sesión es redirigido al
login y uno sin permiso recibe 403. Desde el formulario de usuario se asignan grupos y permisos directos.

Protecciones: solo un superusuario ve o edita superusuarios y marca `is_superuser`/`is_staff`; nadie puede eliminarse a sí
mismo ni editar sus propios grupos y permisos; los grupos base y los permisos que usa la aplicación no se pueden eliminar.

## Convenciones

- Los valores que cambian entre equipos (base de datos, claves, correo) van en `.env`, que no se sube a Git.
- Los modelos nuevos que se relacionen con usuarios deben usar `settings.AUTH_USER_MODEL`, no `django.contrib.auth.models.User`.

## API de reportes

| Método y ruta | Quién | Qué hace |
|---|---|---|
| `GET /feed/api/reports/` | sesión iniciada | Lista paginada de reportes activos sin resolver. Filtros: `?species=PERRO`, `?status=PERDIDO`, `?search=texto`, `?page=2` |
| `GET /feed/api/reports/mine/` | sesión iniciada | Todos mis reportes (incluye los resueltos) |
| `GET /feed/api/reports/<id>/` | sesión iniciada | Detalle |
| `POST /feed/api/reports/` | permiso `feed.add_petreport` | Crear (multipart con la foto en `image`) |
| `PATCH /feed/api/reports/<id>/` | dueño con `feed.change_petreport`, o `feed.moderar_reportes` | Editar, también `is_resolved` |
| `DELETE /feed/api/reports/<id>/` | dueño con `feed.delete_petreport`, o `feed.moderar_reportes` | Eliminar (borra también la foto) |

Las pantallas llaman a la API con `PetsAlert.api(...)`, definido en `static/js/petsalert.js`.

## API del chat

Cada chat pertenece a un reporte y une al dueño del reporte con una persona interesada (uno por pareja reporte-interesado).
Todas las rutas exigen sesión y el permiso `chat.usar_chat`. Solo los dos participantes pueden ver un chat.

| Método y ruta | Qué hace |
|---|---|
| `GET /chat/api/chats/` | Mis chats, con el reporte, la otra persona, el último mensaje y los mensajes sin leer |
| `POST /chat/api/chats/` con `{"report": <id>}` | Abre el chat de ese reporte, o devuelve el que ya existe |
| `GET /chat/api/chats/<id>/messages/` | Mensajes del chat. Con `?after=<id>` solo los más nuevos. Marca como leídos los de la otra persona |
| `POST /chat/api/chats/<id>/messages/` con `{"content": "..."}` | Envía un mensaje (máx. 2000 caracteres) |

Las pantallas consultan mensajes nuevos cada 3 segundos (y la lista de chats cada 10) mientras están visibles.
No hay WebSockets; si en el futuro se necesita tiempo real, se puede cambiar esa parte sin tocar los modelos.

## API del perfil

`GET` y `PATCH /profile/api/me/`: nombre, teléfono y localidad. El correo, la foto y el rol no se pueden cambiar desde ahí.
