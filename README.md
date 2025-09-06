# CineVibes
#### Video de nuestro proyecto:
https://youtu.be/D89ms2vA4As


#### Description:
## Funcionalidades principales
CineVibes es una plataforma web que permite a los usuarios:

- **Ver películas**: Accede a una amplia selección de títulos.
- **Recomendar y comentar**: Comparte tus opiniones y sugerencias con otros usuarios.
- **Solicitar películas**: Pide que se añadan títulos que no estén disponibles en la plataforma.
##
### Tecnologías Utilizadas
- *Flask*: Framework de Python para el desarrollo web.
- *SQLite*: Base de datos ligera para almacenar información de usuarios, películas y reseñas.
- *HTML/CSS*: Para la creación de la interfaz de usuario.
- *Flask-WTF*: Para la gestión de formularios y validaciones.
##
### Arquitectura de la aplicacion
La aplicación sigue una estructura modular:
- **Controladores**: Manejan la lógica de negocio (autenticación, gestión de películas y reseñas).
- **Modelos**: Representan los datos y las interacciones con la base de datos.
- **Vistas**: Se encargan de renderizar las páginas que ven los usuarios.

### Características Principales
- **Registro y Autenticación**: Los usuarios pueden registrarse y verificar su cuenta a través de un correo electrónico.
- **Gestión de Perfiles**: Los usuarios pueden editar su información personal y subir fotos de perfil.
- **Búsqueda y Recomendación de Películas**: Funcionalidad para buscar películas y recibir recomendaciones basadas en preferencias.
- **Reseñas y Favoritos**: Los usuarios pueden dejar reseñas sobre las películas y marcarlas como favoritas, pueden eliminar sus comentarios o eliminarlos.

### Interfaz de Usuario
La interfaz es intuitiva y fácil de navegar. Incluye páginas para:
- La página principal con una lista de películas.
- Un formulario para editar el perfil del usuario.
- Resultados de búsqueda y detalles de películas.

### Base de Datos
La base de datos está estructurada en varias tablas:
- **Usuarios**: Almacena información de los usuarios, incluyendo credenciales y estado de verificación.
- **Películas**: Contiene detalles sobre las películas disponibles en la aplicación.
- **Reseñas**: Guarda las opiniones y calificaciones de los usuarios sobre las películas.

### Seguridad
- **Manejo de Contraseñas**: Las contraseñas se almacenan de forma segura utilizando hashing.
- **Validación de Entradas**: Se implementan validaciones para prevenir inyecciones SQL y asegurar la integridad de los datos.

### Pruebas y Depuración
Se realizaron pruebas exhaustivas para garantizar el correcto funcionamiento de todas las funcionalidades. Se implementaron manejadores de errores para informar a los usuarios sobre problemas.

### Despliegue
La aplicación se puede desplegar en un servidor utilizando un entorno de producción adecuado. Se han establecido prácticas para el mantenimiento y la actualización de la aplicación.

Variables necesarias para Storage (opcional):
- SUPABASE_URL
- SUPABASE_SERVICE_KEY (o SUPABASE_KEY / SUPABASE_ANON_KEY si el bucket es público y permite escritura con esa clave)
- SUPABASE_BUCKET (por defecto: profile-pics)
##
### Controllers
El código implementa varios controladores para gestionar diferentes aspectos de una aplicación web. **AuthController** se encarga del registro y la gestión de usuarios, utilizando la biblioteca `sqlite3` para almacenar información de manera eficiente. Al registrar un nuevo usuario, genera un código de verificación único y lo envía por correo electrónico, asegurando que el usuario tenga acceso a su cuenta. Además, permite la verificación del código, actualizando el estado del usuario a verificado y ofreciendo funcionalidades para gestionar su perfil, como la actualización de datos personales y contraseñas.

Por otro lado, el **MovieController** gestiona la búsqueda y obtención de detalles sobre películas. Utiliza un modelo de película y la API de IMDb para interactuar con la base de datos y proporcionar información actualizada. Su método principal permite buscar películas según una consulta, filtrando los resultados y verificando la disponibilidad en la base de datos. También incluye métodos para obtener detalles específicos de una película y ofrece recomendaciones aleatorias, mejorando así la experiencia del usuario al interactuar con la aplicación.

El **ReviewController** se ocupa de la creación, recuperación, actualización y eliminación de reseñas. Almacena las reseñas en una base de datos SQLite y permite a los usuarios añadir reseñas para películas específicas. Incluye métodos para recuperar reseñas de usuarios y películas, así como para modificar o eliminar reseñas según la propiedad del usuario. Además, proporciona una vista más completa al incluir detalles de las películas junto con las reseñas, y permite contar el número total de reseñas realizadas por un usuario, facilitando el seguimiento de su actividad en la plataforma.

##
### Styles
Se establecen diferentes colores para elementos clave como el fondo, el texto y los bordes, lo que permite una apariencia cohesiva y atractiva. La estructura general del cuerpo de la página se configura con un fondo de degradado, asegurando que el contenido se visualice correctamente y se mantenga en un diseño flexible y responsivo.

La barra de navegación se estiliza con un degradado y un efecto de sombra, proporcionando un diseño moderno. Los enlaces de navegación tienen un efecto de transformación al pasar el mouse, lo que mejora la interactividad. Las tarjetas de películas están diseñadas para ser visualmente atractivas, con un efecto de elevación al pasar el mouse y una disposición que permite que el contenido se apile verticalmente. Esto incluye imágenes de las películas que se ajustan adecuadamente, manteniendo su proporción y asegurando que el diseño sea limpio y ordenado.

Los botones en la interfaz también están estilizados para ofrecer una experiencia de usuario intuitiva, con cambios de color y efectos de elevación al interactuar con ellos. El pie de página utiliza un color de fondo sólido y un diseño que asegura que los enlaces sean visibles y accesibles. Además, se han implementado animaciones suaves que mejoran la experiencia visual al interactuar con diferentes elementos de la página.

El diseño es responsivo, adaptándose a diferentes tamaños de pantalla, lo que garantiza que los usuarios tengan una experiencia óptima sin importar el dispositivo que utilicen. Se incluyen secciones hero con un fondo desenfocado que proporciona un impacto visual, junto con texto destacado que resalta las características importantes de la aplicación. En resumen, el código establece una base sólida para una interfaz de usuario atractiva y funcional, centrada en la experiencia del usuario.

##
### Scripts
El objetivo principal de la script es gestionar las interacciones del usuario con los formularios de registro e inicio de sesión, así como manejar la carga de imágenes de perfil y detectar la presencia de bloqueadores de anuncios. Esto se logra mediante una serie de funciones que se inicializan al cargar el documento.

Una de las funciones más importantes es el manejo del formulario de registro. Cuando el usuario envía este formulario, el script previene el comportamiento por defecto, lo que significa que la página no se recargará. En lugar de eso, se recopilan los datos ingresados, como el apodo, el correo electrónico y la contraseña, y se envían al servidor a través de una solicitud `fetch`. La respuesta del servidor se utiliza para actualizar un mensaje en la interfaz, informando al usuario sobre el resultado de su intento de registro.

De manera similar, el script también gestiona el formulario de inicio de sesión. Al enviar este formulario, se recogen el correo electrónico y la contraseña del usuario, que se envían al servidor. Si el inicio de sesión es exitoso, el usuario es redirigido automáticamente a su perfil. Esta funcionalidad mejora la experiencia del usuario al permitir una navegación fluida sin recargas innecesarias.

Otra característica clave es la detección de bloqueadores de anuncios. Utilizando la biblioteca `fuckAdBlock`, el script determina si un bloqueador está presente. Dependiendo del resultado, se pueden ejecutar diferentes acciones, como mostrar mensajes en la consola. Esto permite al desarrollador tener información sobre la experiencia del usuario y ajustar el contenido de acuerdo a ello.

Además, el script permite a los usuarios cargar una imagen de perfil. Al seleccionar un archivo, se utiliza un `FileReader` para mostrar la imagen en la interfaz de usuario antes de que se complete la carga. También se muestra un indicador de carga mientras se sube la imagen, lo que proporciona retroalimentación visual al usuario.

Se implementa una validación de formularios para asegurar que todos los campos obligatorios sean completados correctamente antes de permitir el envío. Si un formulario no cumple con los requisitos de validación, el envío se previene y se añade una clase que muestra visualmente los errores. Esta funcionalidad es crucial para mejorar la usabilidad y la integridad de los datos ingresados por los usuarios.
##
### Templates
El archivo 404.html se utiliza para mostrar una página de error 404, indicando que la página solicitada no se pudo encontrar.

El archivo 500.html se utiliza para mostrar una página de error 500, indicando un problema en el servidor al procesar la solicitud.

El archivo base.html contiene la estructura base o plantilla de la página web, con elementos comunes como el encabezado, el menú de navegación y el pie de página.

El archivo edit_profile.html contiene la página para que los usuarios puedan editar su perfil, como actualizar información personal, cambiar la contraseña, etc.

El archivo favorites.html muestra la página donde los usuarios pueden ver y administrar sus elementos favoritos, como películas, series, etc.

El archivo index.html es el archivo principal o de inicio de la aplicación web, que contiene la página principal o de bienvenida.

El archivo login.html contiene la página de inicio de sesión, donde los usuarios pueden ingresar sus credenciales para acceder a la aplicación.

El archivo movie_detail.html muestra los detalles de una película específica, como sinopsis, elenco, calificaciones, etc.

El archivo movie_player.html contiene el reproductor de video o multimedia para ver las películas.

El archivo profile.html contiene la página de perfil de usuario, donde se muestra la información personal y las preferencias del usuario.

El archivo recommend.html muestra las recomendaciones de películas o contenido basadas en las preferencias del usuario.

El archivo register.html contiene el formulario de registro para que los nuevos usuarios puedan crear una cuenta.

El archivo request_movie.html permite a los usuarios solicitar o sugerir nuevas películas o contenido para que se agregue a la aplicación.

El archivo search.html contiene el formulario y la funcionalidad de búsqueda de la aplicación.

El archivo verify.html se utiliza para la verificación de cuentas de usuario, como la confirmación de correo electrónico.

El archivo user_profile proporciona toda la informacion del usuario para que su perfil sea visible para los demas usuarios y asi ver sus reviews, etc.
