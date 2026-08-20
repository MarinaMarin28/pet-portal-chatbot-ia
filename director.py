"""Orquestador híbrido del chatbot.

El director decide la intención del usuario, consulta los datos que necesita
(catálogo del backend) y devuelve una respuesta estructurada para que el front
la renderice como burbujas, chips de opciones o acciones (login/registro/agenda).

Híbrido: las opciones, datos y acciones son deterministas (confiables); el LLM
solo participa en la clasificación de la consulta libre y queda reservado para
redactar respuestas de 'Otros' en futuras mejoras.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from catalog import (
    crear_mascota_publica,
    crear_turno_publico,
    obtener_centros,
    obtener_centros_por_especialidad,
    obtener_dias_disponibles,
    obtener_especialidades,
    obtener_horarios,
    obtener_horarios_disponibles,
    obtener_productos,
    obtener_profesionales_por_especialidad,
)
from llm import llm
from prompts import (
    ACCION_IR_AGENDA,
    ACCION_LOGIN,
    ACCION_RESERVAR_SIN_CUENTA,
    DIAS_SEMANA,
    MENSAJE_CENTROS,
    MENSAJE_CRONOGRAMA,
    MENSAJE_CRONOGRAMA_GATOS,
    MENSAJE_CRONOGRAMA_PERROS,
    MENSAJE_ERROR_CATALOGO,
    MENSAJE_ERROR_OPCION,
    MENSAJE_ESPECIALIDADES,
    MENSAJE_OTROS,
    MENSAJE_PRODUCTOS,
    MENSAJE_TURNO_CONFIRMACION,
    MENSAJE_TURNO_CENTRO,
    MENSAJE_TURNO_DIA,
    MENSAJE_TURNO_ESPECIALIDAD,
    MENSAJE_TURNO_ESPECIE,
    MENSAJE_TURNO_ERROR,
    MENSAJE_TURNO_ES_CLIENTE,
    MENSAJE_TURNO_EXITO,
    MENSAJE_TURNO_HORA,
    MENSAJE_TURNO_LOGIN_REQUERIDO,
    MENSAJE_TURNO_NOMBRE_DUENIO,
    MENSAJE_TURNO_NOMBRE_MASCOTA,
    MENSAJE_TURNO_PROFESIONAL,
    MENSAJE_TURNO_REDIRECCION,
    OPCIONES_ESPECIE,
    OPCIONES_ESPECIE_TURNO,
    OPCIONES_ES_CLIENTE,
    OPCIONES_LISTA,
    OPCIONES_MENU,
    OPCIONES_TRAS_CRONOGRAMA_GATOS,
    OPCIONES_TRAS_CRONOGRAMA_PERROS,
    OPCIONES_TURNO,
    OPCION_VOLVER,
    PROMPT_CLASIFICACION,
    SALUDO,
    SIN_CENTROS,
    SIN_ESPECIALIDADES,
    SIN_HORARIOS,
    SIN_PRODUCTOS,
)

logger = logging.getLogger("director")

# Estado en memoria de la reserva de turno por sesión de chat. El microservicio
# es stateless entre mensajes, así que las selecciones de cada conversación se
# acumulan acá (la clave es la sesionId de la conversación).
_estado_turno: dict[str, dict[str, Any]] = {}

_INTENCIONES_VALIDAS = {
    "especialidades",
    "horarios_especialidad",
    "productos",
    "centros",
    "solicitar_turno",
    "cronograma",
    "menu",
    "otros",
}

_PALABRAS_CLAVE: dict[str, list[str]] = {
    "solicitar_turno": ["turno", "reservar", "agendar", "sacá", "sacar", "turno", "cita"],
    "especialidades": ["especialidad", "especialidades"],
    "horarios_especialidad": ["horario", "horarios", "días", "dias", "atiende"],
    "productos": ["producto", "productos", "alimento", "mercado", "comprar", "precio"],
    "centros": ["centro", "centros", "sucursal", "sucursales", "dirección", "direccion", "dónde", "donde"],
    "cronograma": [
        "vacuna",
        "vacunas",
        "cronograma",
        "desparasitación",
        "desparasitacion",
        "antirrábica",
        "antirrabica",
        "séxtuple",
        "sextuple",
        "triple felina",
        "leucemia",
        "cachorro",
        "cachorros",
        "gatito",
        "gatitos",
    ],
    "menu": ["hola", "menu", "menú", "ayuda", "empezar", "opciones"],
}

_clasificacion_chain = (
    ChatPromptTemplate.from_messages([("system", PROMPT_CLASIFICACION)])
    | llm
)


async def procesar(payload: dict[str, Any]) -> dict[str, Any]:
    opcion = payload.get("opcion")
    mensaje = (payload.get("mensaje") or "").strip()
    especialidad_id = payload.get("especialidadId")
    usuario_logueado = bool(payload.get("usuarioLogueado"))
    historial = payload.get("historial") or []

    # Saludo inicial: sin mensaje y sin historial, o opción explícita "inicio".
    if opcion == "inicio" or (not mensaje and not historial):
        return _respuesta(SALUDO, tipo="inicio", opciones=OPCIONES_MENU)

    if opcion == "volver_menu" or mensaje.lower() in ("volver al menú", "volver al menu"):
        _estado_turno.pop(payload.get("sesionId") or "", None)
        return _respuesta(SALUDO, tipo="inicio", opciones=OPCIONES_MENU)

    if opcion == "especialidades":
        return await _iniciar_reserva(payload)

    if opcion == "horarios_especialidad":
        return await _listar_horarios(especialidad_id, mensaje)

    if opcion == "productos":
        return await _listar_productos()

    if opcion == "centros":
        return await _listar_centros()

    if opcion == "cronograma":
        return _elegir_cronograma()

    if opcion == "cronograma_perros":
        return _mostrar_cronograma_perros()

    if opcion == "cronograma_gatos":
        return _mostrar_cronograma_gatos()

    if opcion == "solicitar_turno":
        return await _iniciar_reserva(payload)

    if opcion == "otros":
        return _respuesta(
            MENSAJE_OTROS,
            tipo="texto_libre",
            opciones=OPCIONES_LISTA,
            guardar_consulta=True,
        )

    # Pasos de la reserva de turno guiada (las opciones llevan la selección).
    if isinstance(opcion, str) and opcion.startswith("turno_"):
        return await _gestionar_turno(payload, opcion)

    # Respuesta en texto libre a la pregunta "¿Sos cliente de Pet Portal?".
    sesion_id = payload.get("sesionId") or ""
    estado = _estado_turno.get(sesion_id, {})
    if estado.get("hora") and "esCliente" not in estado:
        respuesta_cliente = _interpretar_es_cliente_texto(mensaje)
        if respuesta_cliente:
            return await _gestionar_turno(
                payload, f"turno_es_cliente:{respuesta_cliente}"
            )

    # Consulta libre: clasificar intención (LLM con fallback por palabras clave).
    intencion = await _clasificar_intencion(mensaje, _ultimo_asistente(historial))
    if intencion == "especialidades":
        return await _listar_especialidades()
    if intencion == "productos":
        return await _listar_productos()
    if intencion == "centros":
        return await _listar_centros()
    if intencion == "solicitar_turno":
        return await _iniciar_reserva(payload)
    if intencion == "menu":
        return _respuesta(SALUDO, tipo="inicio", opciones=OPCIONES_MENU)
    if intencion == "horarios_especialidad":
        # Si el mensaje nombra una especialidad, la resolvemos por nombre.
        return await _listar_horarios(None, mensaje)
    if intencion == "cronograma":
        # Si el mensaje nombra la especie, mostramos su cronograma directo.
        mensaje_lower = mensaje.lower()
        if "gato" in mensaje_lower or "gata" in mensaje_lower:
            return _mostrar_cronograma_gatos()
        if "perro" in mensaje_lower or "perra" in mensaje_lower:
            return _mostrar_cronograma_perros()
        return _elegir_cronograma()

    # Por defecto se trata como "Otros": mensaje genérico + registro para evaluación.
    return _respuesta(
        MENSAJE_OTROS,
        tipo="texto_libre",
        opciones=OPCIONES_LISTA,
        guardar_consulta=True,
    )


async def _listar_especialidades() -> dict[str, Any]:
    especialidades = await obtener_especialidades()
    if not especialidades:
        return _respuesta(SIN_ESPECIALIDADES, tipo="error", opciones=OPCIONES_LISTA)
    opciones = [e.get("name") or "Sin nombre" for e in especialidades]
    return _respuesta(
        MENSAJE_ESPECIALIDADES,
        tipo="opciones",
        opciones=opciones,
        datos=especialidades,
    )


async def _listar_horarios(
    especialidad_id: Any, nombre: str
) -> dict[str, Any]:
    especialidad_id = especialidad_id or await _resolver_especialidad_por_nombre(nombre)
    if not especialidad_id:
        # Sin especialidad identificada, volvemos a listarlas para elegir.
        return await _listar_especialidades()

    horarios = await obtener_horarios(str(especialidad_id))
    if not horarios:
        return _respuesta(SIN_HORARIOS, tipo="error", opciones=OPCIONES_LISTA)

    mensaje = _armar_mensaje_horarios(horarios)
    return _respuesta(
        mensaje,
        tipo="informacion",
        opciones=OPCIONES_TURNO,
        datos=horarios,
    )


async def _listar_productos() -> dict[str, Any]:
    productos = await obtener_productos()
    if not productos:
        return _respuesta(SIN_PRODUCTOS, tipo="error", opciones=OPCIONES_LISTA)
    mensaje = _armar_mensaje_productos(productos)
    return _respuesta(mensaje, tipo="informacion", opciones=OPCIONES_LISTA, datos=productos)


async def _listar_centros() -> dict[str, Any]:
    centros = await obtener_centros()
    if not centros:
        return _respuesta(SIN_CENTROS, tipo="error", opciones=OPCIONES_LISTA)
    mensaje = _armar_mensaje_centros(centros)
    return _respuesta(mensaje, tipo="informacion", opciones=OPCIONES_LISTA, datos=centros)


def _elegir_cronograma() -> dict[str, Any]:
    return _respuesta(
        MENSAJE_CRONOGRAMA,
        tipo="opciones",
        opciones=OPCIONES_ESPECIE,
    )


def _mostrar_cronograma_perros() -> dict[str, Any]:
    return _respuesta(
        MENSAJE_CRONOGRAMA_PERROS,
        tipo="informacion",
        opciones=OPCIONES_TRAS_CRONOGRAMA_PERROS,
    )


def _mostrar_cronograma_gatos() -> dict[str, Any]:
    return _respuesta(
        MENSAJE_CRONOGRAMA_GATOS,
        tipo="informacion",
        opciones=OPCIONES_TRAS_CRONOGRAMA_GATOS,
    )


async def _iniciar_reserva(payload: dict[str, Any]) -> dict[str, Any]:
    sesion_id = payload.get("sesionId") or ""
    _estado_turno[sesion_id] = {}
    return await _elegir_especialidad_turno(sesion_id)


async def _gestionar_turno(payload: dict[str, Any], opcion: str) -> dict[str, Any]:
    sesion_id = payload.get("sesionId") or ""
    _estado_turno.setdefault(sesion_id, {})
    prefijo, _, valor = opcion.partition(":")

    if prefijo == "turno_especialidad":
        return await _elegir_centro_turno(sesion_id, valor)
    if prefijo == "turno_centro":
        return await _elegir_profesional_turno(sesion_id, valor)
    if prefijo == "turno_profesional":
        return await _elegir_dia_turno(sesion_id, valor)
    if prefijo == "turno_dia":
        return await _elegir_hora_turno(sesion_id, valor)
    if prefijo == "turno_hora":
        return await _procesar_hora_turno(sesion_id, valor)
    if prefijo == "turno_es_cliente":
        return await _procesar_es_cliente_turno(payload, sesion_id, valor)
    if prefijo == "turno_nombre_duenio":
        return _procesar_nombre_duenio_turno(
            sesion_id, payload.get("mensaje") or ""
        )
    if prefijo == "turno_nombre_mascota":
        return _procesar_nombre_mascota_turno(
            sesion_id, payload.get("mensaje") or ""
        )
    if prefijo == "turno_especie":
        return _procesar_especie_turno(sesion_id, valor)
    if prefijo == "turno_reservar":
        return await _reservar_turno(sesion_id)
    return _respuesta(MENSAJE_ERROR_OPCION, tipo="error", opciones=[OPCION_VOLVER])


async def _elegir_especialidad_turno(sesion_id: str) -> dict[str, Any]:
    especialidades = await obtener_especialidades()
    if not especialidades:
        return _respuesta(
            SIN_ESPECIALIDADES, tipo="error", opciones=OPCIONES_LISTA
        )
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["especialidades"] = {
        (e.get("id") or ""): (e.get("name") or "Sin nombre") for e in especialidades
    }
    return _respuesta(
        MENSAJE_TURNO_ESPECIALIDAD,
        tipo="turno_especialidad",
        opciones=[e.get("name") or "Sin nombre" for e in especialidades],
        datos=especialidades,
    )


async def _elegir_centro_turno(
    sesion_id: str, especialidad_id: str
) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["especialidadId"] = especialidad_id
    estado["especialidadNombre"] = (
        estado.get("especialidades", {}).get(especialidad_id) or especialidad_id
    )
    centros = await obtener_centros_por_especialidad(especialidad_id)
    if not centros:
        return _respuesta(
            "Uy, por ahora no hay centros con esa especialidad. "
            "Probá elegir otra especialidad.",
            tipo="error",
            opciones=[OPCION_VOLVER],
        )
    estado["centros"] = {
        (c.get("id") or ""): (c.get("name") or "Sin nombre") for c in centros
    }
    return _respuesta(
        MENSAJE_TURNO_CENTRO,
        tipo="turno_centro",
        opciones=[c.get("name") or "Sin nombre" for c in centros],
        datos=centros,
    )


async def _elegir_profesional_turno(
    sesion_id: str, centro_id: str
) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["centroId"] = centro_id
    estado["centroNombre"] = estado.get("centros", {}).get(centro_id) or centro_id
    profesionales = await obtener_profesionales_por_especialidad(
        estado.get("especialidadId"), centro_id
    )
    if not profesionales:
        return _respuesta(
            "No encontré profesionales disponibles en ese centro para esa "
            "especialidad. Probá elegir otro centro.",
            tipo="error",
            opciones=[OPCION_VOLVER],
        )
    estado["profesionales"] = {
        (p.get("id") or ""): (p.get("name") or "Sin nombre")
        for p in profesionales
    }
    return _respuesta(
        MENSAJE_TURNO_PROFESIONAL,
        tipo="turno_profesional",
        opciones=[p.get("name") or "Sin nombre" for p in profesionales],
        datos=profesionales,
    )


async def _elegir_dia_turno(sesion_id: str, profesional_id: str) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["profesionalId"] = profesional_id
    estado["profesionalNombre"] = (
        estado.get("profesionales", {}).get(profesional_id) or profesional_id
    )
    dias = await obtener_dias_disponibles(
        estado.get("especialidadId"),
        profesional_id,
        estado.get("centroId"),
    )
    if not dias:
        return _respuesta(
            "No encontré días disponibles para ese profesional. "
            "Probá elegir otro profesional.",
            tipo="error",
            opciones=[OPCION_VOLVER],
        )
    opciones: list[str] = []
    datos: list[dict[str, Any]] = []
    for fecha in dias:
        etiqueta = _formatear_dia(str(fecha))
        opciones.append(etiqueta)
        datos.append({"date": str(fecha), "label": etiqueta})
    return _respuesta(
        MENSAJE_TURNO_DIA,
        tipo="turno_dia",
        opciones=opciones,
        datos=datos,
    )


async def _elegir_hora_turno(sesion_id: str, fecha: str) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["fecha"] = fecha
    horarios = await obtener_horarios_disponibles(
        estado.get("especialidadId"),
        estado.get("profesionalId"),
        fecha,
        estado.get("centroId"),
    )
    if not horarios:
        return _respuesta(
            "No encontré horarios disponibles para ese día. "
            "Probá elegir otro día.",
            tipo="error",
            opciones=[OPCION_VOLVER],
        )
    opciones: list[str] = []
    datos: list[dict[str, Any]] = []
    for item in horarios:
        hora = item.get("hora")
        if not hora:
            continue
        etiqueta = _formatear_hora(str(hora))
        opciones.append(etiqueta)
        datos.append({"hora": str(hora), "label": etiqueta})
    return _respuesta(
        MENSAJE_TURNO_HORA,
        tipo="turno_hora",
        opciones=opciones,
        datos=datos,
    )


async def _procesar_hora_turno(sesion_id: str, hora: str) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["hora"] = hora
    return _respuesta(
        MENSAJE_TURNO_ES_CLIENTE.format(
            resumen=_armar_resumen_turno(estado)
        ),
        tipo="turno_es_cliente",
        opciones=OPCIONES_ES_CLIENTE,
    )


async def _procesar_es_cliente_turno(
    payload: dict[str, Any], sesion_id: str, valor: str
) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["esCliente"] = valor == "si"
    if valor == "si":
        if bool(payload.get("usuarioLogueado")):
            return _turno_redireccion(sesion_id)
        return _respuesta(
            MENSAJE_TURNO_LOGIN_REQUERIDO,
            tipo="redireccion",
            url="/login",
            acciones=[
                {"etiqueta": ACCION_LOGIN, "url": "/login", "accion": "iniciar_sesion"}
            ],
            datos=[{"pendiente": _turno_pendiente(estado)}],
        )
    return _respuesta(
        MENSAJE_TURNO_NOMBRE_DUENIO,
        tipo="turno_pedir_nombre_duenio",
        opciones=[OPCION_VOLVER],
    )


def _procesar_nombre_duenio_turno(
    sesion_id: str, nombre: str
) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["nombreDuenio"] = nombre.strip()
    return _respuesta(
        MENSAJE_TURNO_NOMBRE_MASCOTA,
        tipo="turno_pedir_nombre_mascota",
        opciones=[OPCION_VOLVER],
    )


def _procesar_nombre_mascota_turno(
    sesion_id: str, nombre: str
) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["nombreMascota"] = nombre.strip()
    return _respuesta(
        MENSAJE_TURNO_ESPECIE,
        tipo="turno_especie",
        opciones=OPCIONES_ESPECIE_TURNO,
    )


def _procesar_especie_turno(sesion_id: str, especie: str) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    estado["especie"] = especie
    return _respuesta(
        MENSAJE_TURNO_CONFIRMACION.format(
            resumen=_armar_resumen_turno(estado, con_mascota=True)
        ),
        tipo="turno_confirmacion",
        opciones=[ACCION_RESERVAR_SIN_CUENTA, OPCION_VOLVER],
        datos=[{"pendiente": _turno_pendiente(estado)}],
    )


def _turno_redireccion(sesion_id: str) -> dict[str, Any]:
    estado = _estado_turno.setdefault(sesion_id, {})
    return _respuesta(
        MENSAJE_TURNO_REDIRECCION.format(
            resumen=_armar_resumen_turno(estado)
        ),
        tipo="redireccion",
        url="/turnos",
        acciones=[
            {"etiqueta": ACCION_IR_AGENDA, "url": "/turnos", "accion": "ir_agenda"}
        ],
        datos=[{"pendiente": _turno_pendiente(estado)}],
    )


async def _reservar_turno(sesion_id: str) -> dict[str, Any]:
    estado = _estado_turno.get(sesion_id, {})
    nombre_mascota = (estado.get("nombreMascota") or "").strip()
    especie = (estado.get("especie") or "").strip()
    nombre_duenio = (estado.get("nombreDuenio") or "").strip()
    if not nombre_mascota or not nombre_duenio:
        return _respuesta(MENSAJE_TURNO_ERROR, tipo="error", opciones=OPCIONES_LISTA)

    mascota = await crear_mascota_publica(
        {
            "name": nombre_mascota,
            "species": especie,
            "ownerName": nombre_duenio,
        }
    )
    if not mascota:
        return _respuesta(MENSAJE_TURNO_ERROR, tipo="error", opciones=OPCIONES_LISTA)

    turno = await crear_turno_publico(
        {
            "petId": mascota.get("id"),
            "clinicId": estado.get("centroId"),
            "specialtyId": estado.get("especialidadId"),
            "professionalId": estado.get("profesionalId"),
            "date": estado.get("hora"),
            "sesionId": sesion_id,
        }
    )
    if not turno:
        return _respuesta(MENSAJE_TURNO_ERROR, tipo="error", opciones=OPCIONES_LISTA)

    _estado_turno.pop(sesion_id, None)
    return _respuesta(
        MENSAJE_TURNO_EXITO.format(
            resumen=_armar_resumen_turno(estado, con_mascota=True)
        ),
        tipo="turno_exito",
        opciones=[OPCION_VOLVER],
        datos=[{"turno": turno}],
    )


def _turno_pendiente(estado: dict[str, Any]) -> dict[str, Any]:
    return {
        "especialidadId": estado.get("especialidadId"),
        "centroId": estado.get("centroId"),
        "profesionalId": estado.get("profesionalId"),
        "fecha": estado.get("fecha"),
        "horario": estado.get("hora"),
    }


def _armar_resumen_turno(
    estado: dict[str, Any], con_mascota: bool = False
) -> str:
    lineas = [
        f"Especialidad: {estado.get('especialidadNombre') or estado.get('especialidadId') or 'a confirmar'}"
    ]
    if estado.get("centroNombre") or estado.get("centroId"):
        lineas.append(
            f"Centro: {estado.get('centroNombre') or estado.get('centroId')}"
        )
    if estado.get("profesionalNombre") or estado.get("profesionalId"):
        lineas.append(
            f"Profesional: {estado.get('profesionalNombre') or estado.get('profesionalId')}"
        )
    fecha = estado.get("fecha")
    hora = estado.get("hora")
    if fecha:
        fecha_etiqueta = _formatear_dia(str(fecha))
        if hora:
            lineas.append(
                f"Día y hora: {fecha_etiqueta} a las {_formatear_hora(str(hora))}"
            )
        else:
            lineas.append(f"Día: {fecha_etiqueta}")
    if con_mascota:
        mascota = estado.get("nombreMascota") or "tu mascota"
        especie = estado.get("especie") or ""
        dueño = estado.get("nombreDuenio") or ""
        lineas.append(f"Mascota: {mascota}{f' ({especie})' if especie else ''}")
        if dueño:
            lineas.append(f"A nombre de: {dueño}")
    return "\n".join(lineas)


def _formatear_dia(fecha: str) -> str:
    try:
        dt = datetime.strptime(fecha, "%Y-%m-%d")
        dia_semana = DIAS_SEMANA[(dt.weekday() + 1) % 7]
        return f"{dia_semana} {dt.day:02d}/{dt.month:02d}"
    except ValueError:
        return fecha


def _formatear_hora(hora: str) -> str:
    try:
        dt = datetime.fromisoformat(hora.replace("Z", "+00:00"))
        local = dt.astimezone(_zona_horaria_argentina())
        return local.strftime("%H:%M")
    except ValueError:
        return hora[:5]


def _zona_horaria_argentina() -> timezone | ZoneInfo:
    try:
        return ZoneInfo("America/Argentina/Buenos_Aires")
    except Exception:
        return timezone(timedelta(hours=-3))


def _interpretar_es_cliente_texto(mensaje: str) -> str | None:
    texto = mensaje.strip().lower().replace("í", "i")
    if not texto:
        return None
    if "sin cuenta" in texto or texto.startswith("no"):
        return "no"
    if "soy cliente" in texto or texto.startswith("si"):
        return "si"
    return None


async def _clasificar_intencion(mensaje: str, contexto_asistente: str) -> str:
    intento_llm = await _clasificar_con_llm(mensaje, contexto_asistente)
    if intento_llm:
        return intento_llm

    # Fallback por palabras clave.
    mensaje_lower = mensaje.lower()
    for intencion, palabras in _PALABRAS_CLAVE.items():
        if any(palabra in mensaje_lower for palabra in palabras):
            return intencion

    # Si el mensaje coincide con una especialidad, se interpreta como horarios.
    if await _resolver_especialidad_por_nombre(mensaje):
        return "horarios_especialidad"

    return "otros"


async def _clasificar_con_llm(mensaje: str, contexto_asistente: str) -> str | None:
    try:
        resultado = await asyncio.wait_for(
            _clasificacion_chain.ainvoke(
                {
                    "mensaje": mensaje,
                    "contexto_asistente": contexto_asistente or "(sin contexto)",
                }
            ),
            timeout=15,
        )
        texto = resultado if isinstance(resultado, str) else str(resultado)
        inicio = texto.find("{")
        fin = texto.rfind("}") + 1
        if inicio == -1 or fin == 0:
            return None
        datos = json.loads(texto[inicio:fin])
        intencion = str(datos.get("intencion", "")).strip().lower()
        return intencion if intencion in _INTENCIONES_VALIDAS else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallo clasificación con LLM: %s", exc)
        return None


async def _resolver_especialidad_por_nombre(nombre: str) -> str | None:
    if not nombre:
        return None
    nombre_lower = nombre.strip().lower()
    especialidades = await obtener_especialidades()
    for especialidad in especialidades:
        if (especialidad.get("name") or "").strip().lower() == nombre_lower:
            return especialidad.get("id")
    return None


def _armar_mensaje_horarios(horarios: list[dict[str, Any]]) -> str:
    lineas = ["Estos son los horarios de atención:", ""]
    por_profesional: dict[str, dict[str, Any]] = {}
    for horario in horarios:
        clave = horario.get("professionalId") or horario.get("professionalName") or "Profesional"
        if clave not in por_profesional:
            por_profesional[clave] = {
                "nombre": horario.get("professionalName") or "Profesional",
                "clinica": horario.get("clinicName") or "",
                "bloques": [],
            }
        dia = DIAS_SEMANA[int(horario.get("dayOfWeek", 0)) % 7]
        bloque = f"{dia} de {horario.get('startTime')} a {horario.get('endTime')}hs"
        por_profesional[clave]["bloques"].append(bloque)

    for info in por_profesional.values():
        clinica = f" · {info['clinica']}" if info["clinica"] else ""
        lineas.append(f"• {info['nombre']}{clinica}")
        lineas.extend(f"    - {bloque}" for bloque in info["bloques"])

    return "\n".join(lineas)


def _armar_mensaje_centros(centros: list[dict[str, Any]]) -> str:
    lineas = [MENSAJE_CENTROS, ""]
    for centro in centros:
        datos_contacto = [
            centro.get("address"),
            centro.get("phone"),
            centro.get("email"),
        ]
        contacto = " · ".join(str(v) for v in datos_contacto if v)
        nombre = centro.get("name") or "Centro"
        lineas.append(f"• {nombre}" + (f" — {contacto}" if contacto else ""))
    return "\n".join(lineas)


def _armar_mensaje_productos(productos: list[dict[str, Any]]) -> str:
    lineas = [MENSAJE_PRODUCTOS, ""]
    for producto in productos:
        nombre = producto.get("name") or "Producto"
        precio = producto.get("precioCliente") or producto.get("price")
        marca = producto.get("brand")
        linea = f"• {nombre}"
        if marca:
            linea += f" ({marca})"
        if precio:
            linea += f" — ${precio}"
        lineas.append(linea)
    return "\n".join(lineas)


def _ultimo_asistente(historial: list[dict[str, Any]]) -> str:
    for mensaje in reversed(historial or []):
        if isinstance(mensaje, dict) and mensaje.get("rol") == "asistente":
            contenido = mensaje.get("contenido")
            if contenido:
                return str(contenido)
    return ""


def _respuesta(
    mensaje: str,
    tipo: str = "texto_libre",
    opciones: list[str] | None = None,
    acciones: list[dict[str, str]] | None = None,
    datos: list[dict[str, Any]] | None = None,
    url: str | None = None,
    guardar_consulta: bool = False,
) -> dict[str, Any]:
    return {
        "mensaje": mensaje,
        "tipo": tipo,
        "opciones": opciones or [],
        "acciones": acciones or [],
        "datos": datos or [],
        "url": url,
        "guardarConsulta": guardar_consulta,
    }