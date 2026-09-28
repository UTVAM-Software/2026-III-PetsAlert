# Migración Django: Chat y Profile

Se migraron desde Flutter/Dart a Django + HTML/CSS/JavaScript los flujos existentes de:

- Mensajes (lista de conversaciones)
- Sala de chat
- Mi Perfil
- Mis Reportes
- Privacidad

Firebase Auth y Firestore continúan siendo el backend. No se crearon modelos Django para sustituir los datos de Firebase.

También se integró el bottom navigation equivalente al `HomeScreen` de Flutter con Inicio, Mis Reportes, Mensajes y Perfil.

Los detalles menores pendientes de las vistas ya existentes (feed/login/registro/forgot password) quedan intencionalmente para una etapa posterior, tal como se decidió durante la migración.
