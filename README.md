# EcoRutas Chile

## Ficha del proyecto

- **Nombre de la organización:** EcoRutas Chile.
- **Modelo de negocio / giro:** Agencia de ecoturismo con catálogo de excursiones y solicitud simulada de itinerarios.
- **Integrante:** Francisco Ortiz Gonzalez — RUT 19128074-1.
- **Modalidad:** Trabajo individual 
- **Entidad de contexto (ORM):** `RegionTuristica`.
- **Entidad principal gestionable (ORM):** `Excursion`.
- **Propósito de la sesión (`request.session`):** Seleccionar excursiones, modificar la cantidad de personas, eliminar selecciones y calcular subtotal, recargo comercial del 5% y total. Al confirmar, se genera un comprobante simulado y se vacía el itinerario.

## Instalación y ejecución

### Requisitos

- Python 3.13.
- Conexión a Internet para instalar dependencias y cargar Bootstrap 5.

Abre PowerShell dentro de la carpeta `ecorutas`, donde se encuentra el archivo `manage.py`.

### 1. Crear el entorno virtual

```powershell
python -m venv .venv
```

### 2. Instalar las dependencias

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configurar las variables de entorno

Copia el archivo de ejemplo:

```powershell
Copy-Item .env.example .env
```

Genera una clave para Django:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Abre `.env` y reemplaza el valor de `DJANGO_SECRET_KEY` por la clave generada, entre comillas. Mantén `DJANGO_DEBUG=True` para las pruebas locales.

### 4. Aplicar las migraciones

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

### 5. Cargar los datos iniciales

```powershell
.\.venv\Scripts\python.exe manage.py poblar_datos
```

El comando crea cuatro regiones, ocho excursiones con imágenes y los usuarios de prueba.

### 6. Ejecutar la aplicación

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Abre las siguientes direcciones en el navegador:

- **Aplicación:** http://127.0.0.1:8000/
- **Django Admin:** http://127.0.0.1:8000/admin/

Para detener el servidor, presiona `Ctrl + C`.

## Credenciales de prueba

Estas credenciales corresponden a las contraseñas incluidas en `.env.example`, si no se modifican antes de cargar los datos.

| Tipo de usuario | Usuario | Contraseña |
| --- | --- | --- |
| Administrador | `admin_demo` | `EcoRutas.Admin2026!` |
| Estándar | `viajero_demo` | `EcoRutas.Viajero2026!` |

El administrador puede gestionar excursiones y acceder a Django Admin. El usuario estándar no tiene acceso a las rutas de gestión.

## Bitácora de uso de inteligencia artificial

**Herramienta utilizada:** ChatGPT/Codex..

### Caso 1: Modelado relacional e integridad de datos

**Prompt utilizado — reconstrucción:**

¿Cómo diseñar los modelos RegionTuristica, Excursion y Perfil en Django, utilizando ForeignKey con PROTECT, validadores para tarifas y cupos, estados con choices y baja lógica?

**Respuesta técnica:**

Relacionar las excursiones con las regiones mediante `ForeignKey` y `on_delete=models.PROTECT`. Incorporar `MinValueValidator` en los campos numéricos, `TextChoices` para los estados, `ImageField` para imágenes y un campo booleano para la baja lógica. Asociar el perfil al usuario mediante `OneToOneField`.

**Adaptación aplicada y su justificación:**

Se implementaron modelos propios del ecoturismo. `PROTECT` evita eliminar regiones con excursiones asociadas, los validadores impiden tarifas y cupos negativos y el campo `activa` permite retirar excursiones del catálogo sin destruir sus registros. Estas decisiones conservan la integridad de los datos y permiten gestionar la vigencia de las excursiones.

### Caso 2: Optimización de consultas del catálogo

**Prompt utilizado — reconstrucción:**

¿Cómo combinar búsquedas por código, nombre y descripción con Q, filtros por región, ordenamiento y paginación, evitando consultas adicionales al mostrar la región de cada excursión?

**Respuesta técnica:**

Utilizar objetos `Q` para combinar condiciones de búsqueda, `select_related('region')` para obtener los datos relacionados en una misma consulta y `Paginator` para dividir los resultados. Limitar el ordenamiento a una lista de campos permitidos.

**Adaptación aplicada y su justificación:**

Se incorporó búsqueda simultánea por código, nombre y descripción, filtros regionales y seis excursiones por página. Se aplicó `select_related('region')` para evitar una consulta adicional por cada excursión mostrada. Las opciones de ordenamiento se restringieron a las admitidas por la aplicación, manteniendo un comportamiento controlado del catálogo.

### Caso 3: Seguridad y validación del itinerario

**Prompt utilizado — reconstrucción:**

¿Cómo implementar un itinerario con request.session que valide cupos y precios al confirmar, calcule importes con Decimal y proteja las operaciones mediante CSRF y los permisos administrativos de Django?

**Respuesta técnica:**

Guardar identificadores y cantidades en la sesión, consultar nuevamente disponibilidad y precios antes de confirmar y calcular los importes con `Decimal`. Utilizar POST y tokens CSRF para modificar datos. Proteger las rutas administrativas mediante `login_required` y `user_passes_test(is_staff)`.

**Adaptación aplicada y su justificación:**

El itinerario guarda identificadores de excursiones y cantidades de personas en `request.session`. Al confirmar, se vuelven a comprobar cupos y precios para evitar utilizar información desactualizada. Se calculan subtotal, recargo comercial del 5% y total con `Decimal`, evitando los errores de precisión propios de los números de punto flotante.

Las operaciones que modifican el itinerario requieren POST y CSRF. La gestión se limita a usuarios autenticados con `is_staff`, mientras que el registro público crea cuentas sin privilegios administrativos. Se permite eliminar una excursión aunque haya dejado de estar disponible y, al generar el comprobante simulado, se vacía el itinerario.