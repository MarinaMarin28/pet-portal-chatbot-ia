"""Copias de texto y prompts del asistente virtual.

Toda la copy del flujo guiado vive acá para que sea versionable y controlable,
separada de la lógica de orquestación (director.py).
"""

# --- Saludo y menú principal ---
SALUDO = (
    "Hola! Soy tu asistente virtual del centro médico, "
    "¿en qué puedo ayudarte hoy?"
)
OPCIONES_MENU = ["Especialidades", "Productos", "Centros de atención", "Otros"]
OPCION_VOLVER = "Volver al menú"

# --- Especialidades ---
MENSAJE_ESPECIALIDADES = (
    "¡Genial! Estas son nuestras especialidades disponibles. "
    "Elegí una para ver días, horarios y el especialista que atiende:"
)
SIN_ESPECIALIDADES = (
    "Uy, por ahora no tengo especialidades cargadas. Volvé a intentar más tarde."
)

# --- Horarios por especialidad ---
SIN_HORARIOS = (
    "Todavía no cargaron horarios para esa especialidad. "
    "Volvé al menú y elegí otra opción."
)
DIAS_SEMANA = [
    "Domingo",
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
]
OPCIONES_TURNO = ["Quiero un turno", OPCION_VOLVER]

# --- Productos ---
MENSAJE_PRODUCTOS = (
    "¡Mirá! Estos son algunos de nuestros productos favoritos de los peludos:"
)
SIN_PRODUCTOS = "Todavía no cargamos productos. Volvé a intentar más tarde."
OPCIONES_LISTA = [OPCION_VOLVER]

# --- Centros de atención ---
MENSAJE_CENTROS = (
    "Estos son nuestros centros de atención. "
    "Te paso dirección y teléfono de cada uno:"
)
SIN_CENTROS = "Todavía no cargamos centros de atención. Volvé a intentar más tarde."

# --- Turno ---
MENSAJE_NO_LOGUEADO = (
    "Para poder reservar un turno necesitás iniciar sesión en tu cuenta "
    "de cliente o registrarte. ¡Es súper rápido!"
)
MENSAJE_TURNO_LOGUEADO = (
    "¡Perfecto! Te redirijo a la agenda para que elijas tu turno disponible."
)
ACCION_LOGIN = "Iniciar sesión"
ACCION_REGISTRO = "Registrarme"
ACCION_IR_AGENDA = "Ir a la agenda"

# --- Otros (consulta libre, base para mejoras futuras) ---
MENSAJE_OTROS = (
    "Gracias por tu consulta, en este momento no podré ayudarte "
    "pero estoy mejorando para hacerlo."
)

# --- Fallbacks ---
MENSAJE_ERROR_CATALOGO = (
    "¡Guau! Por un momentito no puedo consultar la información, "
    "pero ya la dejé registrada. Volvé a intentar en unos segundos."
)
MENSAJE_ERROR_OPCION = "No entendí esa opción. Elegí una de las opciones del menú."

# --- Clasificación de intención (solo consulta libre) ---
PROMPT_CLASIFICACION = (
    "Sos el clasificador de intenciones de un asistente virtual de un centro "
    "médico veterinario. Dado el mensaje del cliente y el último mensaje del "
    "asistente, respondé ÚNICAMENTE con un JSON válido con este formato exacto:\n"
    "{{\"intencion\": \"<una de: especialidades, horarios_especialidad, productos, "
    "centros, solicitar_turno, menu, otros>\"}}\n\n"
    "Reglas:\n"
    "- Si el cliente pregunta por especialidades médicas: especialidades.\n"
    "- Si el cliente pide días, horarios o quién atiende una especialidad: horarios_especialidad.\n"
    "- Si el cliente pregunta por productos o compras: productos.\n"
    "- Si el cliente pregunta por sucursales, clínicas, direcciones o centros: centros.\n"
    "- Si el cliente quiere sacar, reservar o agendar un turno: solicitar_turno.\n"
    "- Si es un saludo, o quiere volver al menú: menu.\n"
    "- Cualquier otra consulta general: otros.\n\n"
    "Último mensaje del asistente:\n{contexto_asistente}\n\n"
    "Mensaje del cliente:\n{mensaje}\n\nJSON:"
)

# --- Consulta libre respondida con el modelo (reservada a futuras mejoras) ---
PROMPT_CONSULTA_LIBRE = (
    "Sos el asistente virtual (un perrito amigable) de un centro médico veterinario.\n"
    "Respondé de forma corta (máximo 3 oraciones), alegre, empática y profesional en español.\n"
    "Si no tenés la información, decilo con amabilidad y ofrecé que un humano lo va a contactar.\n\n"
    "Consulta del cliente: {mensaje}"
)