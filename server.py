"""
Unified GastroRAG server — retrieval API + Streamlit UI on one port (8501).

Streamlit runs internally on 8502; this app exposes FastAPI routes and proxies
everything else (including WebSockets) to Streamlit.
"""
from __future__ import annotations

import asyncio
import os

import httpx
import websockets
from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from api import app

STREAMLIT_HOST = os.getenv("STREAMLIT_INTERNAL_HOST", "127.0.0.1")
STREAMLIT_PORT = os.getenv("STREAMLIT_INTERNAL_PORT", "8502")
STREAMLIT_HTTP = f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}"
STREAMLIT_WS = f"ws://{STREAMLIT_HOST}:{STREAMLIT_PORT}"

_HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)


def _filter_response_headers(headers: httpx.Headers) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() not in _HOP_BY_HOP:
            out[key] = value
    return out


async def _proxy_http(request: Request, path: str) -> Response:
    url = f"{STREAMLIT_HTTP}{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    body = await request.body()
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    async with httpx.AsyncClient(timeout=None, follow_redirects=False) as client:
        upstream = await client.request(
            request.method,
            url,
            headers=headers,
            content=body,
        )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=_filter_response_headers(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )


async def _proxy_websocket(websocket: WebSocket, path: str) -> None:
    await websocket.accept()
    query = websocket.scope.get("query_string", b"").decode()
    upstream_url = f"{STREAMLIT_WS}{path}"
    if query:
        upstream_url = f"{upstream_url}?{query}"

    try:
        async with websockets.connect(upstream_url) as upstream:

            async def client_to_upstream() -> None:
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg["type"] == "websocket.disconnect":
                            break
                        if msg.get("text") is not None:
                            await upstream.send(msg["text"])
                        elif msg.get("bytes") is not None:
                            await upstream.send(msg["bytes"])
                except WebSocketDisconnect:
                    pass

            async def upstream_to_client() -> None:
                try:
                    async for message in upstream:
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except Exception:
                    pass

            await asyncio.gather(client_to_upstream(), upstream_to_client())
    except Exception:
        await websocket.close()


@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
async def streamlit_http_proxy(full_path: str, request: Request) -> Response:
    path = f"/{full_path}" if full_path else "/"
    return await _proxy_http(request, path)


@app.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"], include_in_schema=False)
async def streamlit_root_proxy(request: Request) -> Response:
    return await _proxy_http(request, "/")


@app.websocket("/{full_path:path}")
async def streamlit_ws_proxy(websocket: WebSocket, full_path: str) -> None:
    path = f"/{full_path}" if full_path else "/"
    await _proxy_websocket(websocket, path)


@app.websocket("/")
async def streamlit_ws_root(websocket: WebSocket) -> None:
    await _proxy_websocket(websocket, "/")
