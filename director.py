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
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from catalog import (
    obtener_centros,
    obtener_especialidades,
    obtener_horarios,
    obtener_productos,
)
from llm import llm
from prompts import (
    ACCION_IR_AGENDA,
    ACCION_LOGIN,
    ACCION_REGISTRO,
    DIAS_SEMANA,
    MENSAJE_CENTROS,
    MENSAJE_CRONOGRAMA,
    MENSAJE_CRONOGRAMA_GATOS,
    MENSAJE_CRONOGRAMA_PERROS,
    MENSAJE_ERROR_CATALOGO,
    MENSAJE_ERROR_OPCION,
    MENSAJE_ESPECIALIDADES,
    MENSAJE_NO_LOGUEADO,
    MENSAJE_OTROS,
    MENSAJE_PRODUCTOS,
    MENSAJE_TURNO_LOGUEADO,
    OPCIONES_ESPECIE,
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
        return _respuesta(SALUDO, tipo="inicio", opciones=OPCIONES_MENU)

    if opcion == "especialidades":
        return await _listar_especialidades()

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
        return _solicitar_turno(usuario_logueado)

    if opcion == "otros":
        return _respuesta(
            MENSAJE_OTROS,
            tipo="texto_libre",
            opciones=OPCIONES_LISTA,
            guardar_consulta=True,
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
        return _solicitar_turno(usuario_logueado)
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


def _solicitar_turno(usuario_logueado: bool) -> dict[str, Any]:
    if not usuario_logueado:
        return _respuesta(
            MENSAJE_NO_LOGUEADO,
            tipo="autenticacion",
            opciones=[ACCION_LOGIN, ACCION_REGISTRO, OPCION_VOLVER],
            acciones=[
                {"etiqueta": ACCION_LOGIN, "url": "/login", "accion": "iniciar_sesion"},
                {"etiqueta": ACCION_REGISTRO, "url": "/registro", "accion": "registrarse"},
            ],
        )
    return _respuesta(
        MENSAJE_TURNO_LOGUEADO,
        tipo="redireccion",
        url="/turnos",
        acciones=[
            {"etiqueta": ACCION_IR_AGENDA, "url": "/turnos", "accion": "ir_agenda"}
        ],
    )


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