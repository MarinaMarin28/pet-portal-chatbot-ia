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


async def _consultar(
    recurso: str, especialidad: str | None = None
) -> list[dict[str, Any]]:
    params: dict[str, str] = {"recurso": recurso}
    if especialidad:
        params["especialidad"] = especialidad

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