"""Cliente HTTP del catálogo del backend NestJS.

El chatbot es quien decide qué datos necesita y los consulta bajo demanda
al endpoint interno `GET /chat/catalogo` del backend, que es el dueño de la BD.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config import BACKEND_API_URL, CHATBOT_TOKEN

logger = logging.getLogger("catalog")

CATALOGO_URL = f"{BACKEND_API_URL}/chat/catalogo"


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if CHATBOT_TOKEN:
        headers["X-Chatbot-Token"] = CHATBOT_TOKEN
    return headers


async def obtener_especialidades() -> list[dict[str, Any]]:
    return await _consultar("especialidades")


async def obtener_horarios(especialidad: str) -> list[dict[str, Any]]:
    return await _consultar("horarios", especialidad=especialidad)


async def obtener_productos() -> list[dict[str, Any]]:
    return await _consultar("productos")


async def obtener_centros() -> list[dict[str, Any]]:
    return await _consultar("centros")


async def obtener_centros_por_especialidad(
    especialidad: str,
) -> list[dict[str, Any]]:
    return await _consultar(
        "centros_por_especialidad", especialidad=especialidad
    )


async def obtener_profesionales_por_especialidad(
    especialidad: str, centro_id: str | None = None
) -> list[dict[str, Any]]:
    return await _consultar(
        "profesionales_por_especialidad",
        especialidad=especialidad,
        centro_id=centro_id,
    )


async def obtener_dias_disponibles(
    especialidad: str,
    profesional_id: str,
    centro_id: str | None = None,
) -> list[dict[str, Any]]:
    return await _consultar(
        "dias_disponibles",
        especialidad=especialidad,
        profesional_id=profesional_id,
        centro_id=centro_id,
    )


async def obtener_horarios_disponibles(
    especialidad: str,
    profesional_id: str,
    fecha: str,
    centro_id: str | None = None,
) -> list[dict[str, Any]]:
    return await _consultar(
        "horarios_disponibles",
        especialidad=especialidad,
        profesional_id=profesional_id,
        centro_id=centro_id,
        fecha=fecha,
    )


async def crear_mascota_publica(datos: dict[str, Any]) -> dict[str, Any] | None:
    return await _enviar_post("pets", datos)


async def crear_turno_publico(datos: dict[str, Any]) -> dict[str, Any] | None:
    return await _enviar_post("appointments", datos)


async def _consultar(
    recurso: str,
    especialidad: str | None = None,
    centro_id: str | None = None,
    profesional_id: str | None = None,
    fecha: str | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {"recurso": recurso}
    if especialidad:
        params["especialidad"] = especialidad
    if centro_id:
        params["centroId"] = centro_id
    if profesional_id:
        params["profesionalId"] = profesional_id
    if fecha:
        params["fecha"] = fecha

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(CATALOGO_URL, params=params, headers=_headers())
            if resp.status_code != 200:
                logger.warning(
                    "Catálogo %s respondió %s: %s", recurso, resp.status_code, resp.text[:200]
                )
                return []
            body = resp.json()
            if isinstance(body, list):
                return body
            datos = body.get("datos") if isinstance(body, dict) else None
            return datos if isinstance(datos, list) else []
    except Exception as exc:  # noqa: BLE001
        logger.error("Error consultando catálogo %s: %s", recurso, exc)
        return []


async def _enviar_post(path: str, datos: dict[str, Any]) -> dict[str, Any] | None:
    url = f"{BACKEND_API_URL}/public/{path}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=datos, headers=_headers())
            if resp.status_code not in (200, 201):
                logger.warning(
                    "POST /public/%s respondió %s: %s",
                    path,
                    resp.status_code,
                    resp.text[:200],
                )
                return None
            body = resp.json()
            return body if isinstance(body, dict) else None
    except Exception as exc:  # noqa: BLE001
        logger.error("Error en POST /public/%s: %s", path, exc)
        return None