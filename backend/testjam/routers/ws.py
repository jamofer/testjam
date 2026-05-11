"""Multi-topic WebSocket endpoint.

Single connection, many topics. Clients send:

    {"action": "subscribe", "topic": "project:42"}
    {"action": "unsubscribe", "topic": "execution:7"}
    {"action": "pong"}

Server replies with:

    {"event": "subscribed", "topic": "..."}
    {"event": "unsubscribed", "topic": "..."}
    {"event": "ping"}
    {"event": "error", "topic": "...", "error": "<reason>"}

Auth: JWT bearer passed via ``?token=...`` query param (same scheme as the
legacy ``/notifications/ws``). Per-topic ACL is enforced at subscribe time —
unauthorized topics get an error ack and the socket stays open.

A background heartbeat task emits ``{"event": "ping"}`` every
``HEARTBEAT_INTERVAL_SECONDS`` so clients behind idle-cutting proxies can
detect a zombie connection and reconnect.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from testjam.auth.security import decode_token
from testjam.database import get_db
from testjam.models.execution import TestExecution
from testjam.models.project import Project
from testjam.models.user import User
from testjam.realtime import manager

router = APIRouter(tags=["WebSocket"])

HEARTBEAT_INTERVAL_SECONDS = 30


def _authenticate_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    username = decode_token(token)
    if not username:
        return None
    return (
        db.query(User)
        .filter(User.username == username, User.is_active == True)  # noqa: E712
        .first()
    )


def _parse_topic(topic: str) -> tuple[str, int] | None:
    if not isinstance(topic, str) or ":" not in topic:
        return None
    kind, _, ident = topic.partition(":")
    try:
        return kind, int(ident)
    except ValueError:
        return None


def _check_user_topic(user: User, target_id: int) -> str | None:
    return None if target_id == user.id else "forbidden"


def _check_project_topic(db: Session, target_id: int) -> str | None:
    return None if db.get(Project, target_id) else "not_found"


def _check_execution_topic(db: Session, target_id: int) -> str | None:
    execution = db.get(TestExecution, target_id)
    if not execution:
        return "not_found"
    return _check_project_topic(db, execution.project_id)


def _authorize_topic(db: Session, user: User, topic: str) -> str | None:
    """Return error code, or None if subscription is allowed."""
    parsed = _parse_topic(topic)
    if parsed is None:
        return "invalid_topic"
    kind, target_id = parsed
    if kind == "user":
        return _check_user_topic(user, target_id)
    if kind == "project":
        return _check_project_topic(db, target_id)
    if kind == "execution":
        return _check_execution_topic(db, target_id)
    return "invalid_topic"


async def _ack(ws: WebSocket, event: str, topic: str | None = None, **extra) -> None:
    payload: dict = {"event": event}
    if topic is not None:
        payload["topic"] = topic
    payload.update(extra)
    await ws.send_json(payload)


async def _read_message(ws: WebSocket) -> dict | None:
    try:
        msg = await ws.receive_json()
    except ValueError:
        await _ack(ws, "error", error="invalid_json")
        return None
    return msg if isinstance(msg, dict) else {}


async def _handle_subscribe(ws: WebSocket, db: Session, user: User, topic) -> None:
    if not isinstance(topic, str):
        await _ack(ws, "error", topic=topic, error="invalid_topic")
        return
    err = _authorize_topic(db, user, topic)
    if err:
        await _ack(ws, "error", topic=topic, error=err)
        return
    await manager.subscribe(topic, ws)
    await _ack(ws, "subscribed", topic=topic)


async def _handle_unsubscribe(ws: WebSocket, topic) -> None:
    if not isinstance(topic, str):
        await _ack(ws, "error", topic=topic, error="invalid_topic")
        return
    await manager.unsubscribe(topic, ws)
    await _ack(ws, "unsubscribed", topic=topic)


async def _dispatch(ws: WebSocket, db: Session, user: User, msg: dict) -> None:
    action = msg.get("action")
    topic = msg.get("topic")
    if action == "pong":
        return
    if action == "subscribe":
        await _handle_subscribe(ws, db, user, topic)
        return
    if action == "unsubscribe":
        await _handle_unsubscribe(ws, topic)
        return
    await _ack(ws, "error", error="invalid_action")


async def _heartbeat_loop(ws: WebSocket) -> None:
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            await ws.send_json({"event": "ping"})
    except asyncio.CancelledError:
        raise
    except Exception:
        return


@router.websocket("/ws")
async def ws_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    user = _authenticate_token(db, token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    heartbeat_task = asyncio.create_task(_heartbeat_loop(websocket))
    try:
        while True:
            msg = await _read_message(websocket)
            if msg is None:
                continue
            await _dispatch(websocket, db, user, msg)
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        await manager.unsubscribe_all(websocket)
