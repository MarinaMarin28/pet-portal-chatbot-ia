"""Copias de texto y prompts del asistente virtual.

Toda la copy del flujo guiado vive acá para que sea versionable y controlable,
separada de la lógica de orquestación (director.py).
"""

# --- Saludo y menú principal ---
SALUDO = (
    "Hola! Soy Huellita, tu asistente virtual del centro médico, "
    "¿en qué puedo ayudarte hoy?"
)
OPCIONES_MENU = [
    "Especialidades",
    "Productos",
    "Centros de atención",
    "Cronograma de vacunación",
    "Otros",
]
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

# --- Cronograma de vacunación ---
MENSAJE_CRONOGRAMA = (
    "¡Buenísimo! Te paso el cronograma básico de vacunación y desparasitación. "
    "¿Sobre qué mascota lo querés ver?"
)
OPCIONES_ESPECIE = ["Perros", "Gatos", OPCION_VOLVER]
OPCIONES_TRAS_CRONOGRAMA_PERROS = ["Ver cronograma de gatos", OPCION_VOLVER]
OPCIONES_TRAS_CRONOGRAMA_GATOS = ["Ver cronograma de perros", OPCION_VOLVER]
MENSAJE_CRONOGRAMA_PERROS = (
    "Cronograma de vacunación para perros\n\n"
    "Vacunas en cachorros:\n"
    "• Polivalente (séxtuple u óctuple): protege contra moquillo, parvovirus, "
    "hepatitis, adenovirus, parainfluenza y leptospirosis.\n"
    "• Antirrábica: obligatoria por ley.\n"
    "• Opcional: tos de las perreras (Bordetella bronchiseptica).\n\n"
    "Cronograma básico de vacunación:\n"
    "• 6 a 8 semanas (1.5 a 2 meses): 1ª dosis de séxtuple + 1ª desparasitación interna.\n"
    "• 10 a 12 semanas (2.5 a 3 meses): 2ª dosis de séxtuple + refuerzo de desparasitación.\n"
    "• 14 a 16 semanas (3.5 a 4 meses): 3ª dosis de séxtuple + 1ª vacuna antirrábica.\n"
    "• Al año de edad: refuerzo anual de la séxtuple y de la antirrábica. "
    "Se repite una vez al año durante toda su vida adulta.\n\n"
    "Desparasitación interna:\n"
    "• Se inicia a las 2 o 3 semanas de vida.\n"
    "• Se repite cada 15 días hasta los 3 meses.\n"
    "• Luego, una vez al mes hasta los 6 meses.\n"
    "• En la etapa adulta, de forma preventiva cada 3 meses.\n\n"
    "Desparasitación externa (pulgas y garrapatas):\n"
    "• Primera pipeta especial para cachorros a partir de los 45 días / 2 meses "
    "(cuando superen el kilo de peso).\n"
    "• Pastillas masticables desde las 8 semanas y 1.3 a 2 kg según el laboratorio.\n"
    "• La frecuencia (mensual o trimestral) depende de la marca elegida.\n\n"
    "Si tenés dudas, consultá con tu veterinario."
)
MENSAJE_CRONOGRAMA_GATOS = (
    "Cronograma de vacunación para gatos\n\n"
    "Vacunas en gatitos:\n"
    "• Triple felina (trivalente): protege contra la panleucopenia, la calicivirosis "
    "y la rinotraqueítis viral felina.\n"
    "• Leucemia felina (FeLV): protege contra el virus de la leucemia. "
    "Es fundamental testear al gato antes de aplicarla.\n"
    "• Antirrábica: obligatoria por ley.\n\n"
    "Cronograma básico de vacunación:\n"
    "• 8 semanas (2 meses): test de leucemia e inmunodeficiencia (VIF/VILEF) "
    "+ 1ª dosis de vacuna triple felina.\n"
    "• 12 semanas (3 meses): 2ª dosis de vacuna triple felina + 1ª dosis "
    "contra la leucemia.\n"
    "• 16 semanas (4 meses): 2ª dosis contra la leucemia + vacuna antirrábica.\n"
    "• Al año de edad: refuerzo anual de la triple felina, la leucemia y la "
    "antirrábica. Se repite una vez al año durante toda su vida adulta.\n\n"
    "Desparasitación interna:\n"
    "• Se inicia a las 3 o 4 semanas de vida con jarabes o gotas aptas para cachorros.\n"
    "• Se repite cada 15 días hasta los 3 meses.\n"
    "• Luego, una vez al mes hasta los 6 meses.\n"
    "• En la etapa adulta, de forma preventiva cada 3 o 4 meses (especialmente "
    "si sale al exterior).\n\n"
    "Desparasitación externa (pulgas, garrapatas y ácaros de la oreja):\n"
    "• Pipetas especiales para gatitos desde las 6 u 8 semanas de vida "
    "(habitualmente deben superar los 600 g u 800 g de peso).\n"
    "• Comprimidos orales para pulgas desde las 9 semanas o cuando alcanzan 1 kg.\n\n"
    "Importante: jamás uses productos de perros en gatos. La permetrina (común en "
    "pipetas caninas) es altamente tóxica y mortal para los felinos.\n\n"
    "Si tenés dudas, consultá con tu veterinario."
)

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

# --- Reserva de turno guiada ---
MENSAJE_TURNO_ESPECIALIDAD = (
    "¡Dale! Vamos a reservar tu turno. Primero, ¿qué especialidad necesitás?"
)
MENSAJE_TURNO_CENTRO = "¿En qué centro te gustaría atenderte?"
MENSAJE_TURNO_PROFESIONAL = (
    "¿Con qué profesional preferís? Mirá los días y horarios disponibles."
)
MENSAJE_TURNO_DIA = "¿Qué día te conviene?"
MENSAJE_TURNO_HORA = "¿A qué hora preferís?"
MENSAJE_TURNO_ESPECIE = (
    "Para dejar tu reserva, contame un poquito de tu mascota. ¿Qué especie es?"
)
MENSAJE_TURNO_NOMBRE_MASCOTA = "¿Cómo se llama tu mascota?"
MENSAJE_TURNO_NOMBRE_DUENIO = (
    "¿Y cuál es tu nombre para dejar anotado el turno?"
)
OPCIONES_ESPECIE_TURNO = ["Perro", "Gato", "Otro"]
MENSAJE_TURNO_REDIRECCION = (
    "¡Perfecto! Elegiste:\n\n{resumen}\n\nTe redirijo a la agenda para "
    "confirmar tu turno."
)
MENSAJE_TURNO_CONFIRMACION = (
    "Resumen de tu turno:\n\n{resumen}\n\n"
    "Si ya tenés una cuenta, iniciá sesión o registrate para asociarlo a tu perfil. "
    "Si preferís, podés reservarlo sin cuenta y un empleado lo va a vincular "
    "cuando nos visites."
)
ACCION_RESERVAR_SIN_CUENTA = "Reservar sin cuenta"
MENSAJE_TURNO_EXITO = (
    "¡Turno reservado! Te esperamos:\n\n{resumen}\n\n"
    "Como no estás registrado, tu mascota quedó asociada a tu nombre y "
    "un empleado la va a vincular a tu cuenta cuando nos visites."
)
MENSAJE_TURNO_ERROR = (
    "Uy, no pude reservar el turno. Probá de nuevo en unos segundos."
)

# --- Otros (consulta libre, base para mejoras futuras) ---
MENSAJE_OTROS = (
    "Gracias por tu consulta, en este momento no podré ayudarte "
    "pero estoy mejorando para hacerlo."
)

# --- Fallbacks ---
MENSAJE_ERROR_CATALOGO = (
    "Por un momentito no puedo consultar la información, "
    "pero ya la dejé registrada. Volvé a intentar en unos segundos."
)
MENSAJE_ERROR_OPCION = "No entendí esa opción. Elegí una de las opciones del menú."

# --- Clasificación de intención (solo consulta libre) ---
PROMPT_CLASIFICACION = (
    "Sos el clasificador de intenciones de un asistente virtual de un centro "
    "médico veterinario. Dado el mensaje del cliente y el último mensaje del "
    "asistente, respondé ÚNICAMENTE con un JSON válido con este formato exacto:\n"
    "{{\"intencion\": \"<una de: especialidades, horarios_especialidad, productos, "
    "centros, solicitar_turno, cronograma, menu, otros>\"}}\n\n"
    "Reglas:\n"
    "- Si el cliente pregunta por especialidades médicas: especialidades.\n"
    "- Si el cliente pide días, horarios o quién atiende una especialidad: horarios_especialidad.\n"
    "- Si el cliente pregunta por productos o compras: productos.\n"
    "- Si el cliente pregunta por sucursales, clínicas, direcciones o centros: centros.\n"
    "- Si el cliente quiere sacar, reservar o agendar un turno: solicitar_turno.\n"
    "- Si el cliente pregunta por vacunas, desparasitación o el cronograma de vacunación "
    "de una mascota: cronograma.\n"
    "- Si es un saludo, o quiere volver al menú: menu.\n"
    "- Cualquier otra consulta general: otros.\n\n"
    "Último mensaje del asistente:\n{contexto_asistente}\n\n"
    "Mensaje del cliente:\n{mensaje}\n\nJSON:"
)

# --- Consulta libre respondida con el modelo (reservada a futuras mejoras) ---
PROMPT_CONSULTA_LIBRE = (
    "Sos Huellita, el asistente virtual (un perrito amigable) de un centro médico veterinario.\n"
    "Respondé de forma corta (máximo 3 oraciones), alegre, empática y profesional en español.\n"
    "Si no tenés la información, decilo con amabilidad y ofrecé que un humano lo va a contactar.\n\n"
    "Consulta del cliente: {mensaje}"
)