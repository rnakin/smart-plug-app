"""
Real-time escalation engine for per-device usage timers.

Three-stage escalation triggered after a PlugSession is created:
  1. notify  — soft toast  (device.until_notify_minutes)
  2. alert   — loud modal + sound  (device.until_alert_minutes)
  3. cutoff  — auto power-off      (device.until_cutoff_minutes)

Timers restart from zero when the user clicks "Yes, reset timer".
All timers are cancelled when the session ends (NFC removed, or user cuts off).
"""

import threading
import logging
from django.db import close_old_connections

logger = logging.getLogger(__name__)

# session_id (str) → {'notify': Timer, 'alert': Timer, 'cutoff': Timer}
_timers: dict = {}
_timers_lock = threading.Lock()


# ── Public API ────────────────────────────────────────────────────────────────

def schedule_escalation(session_id: str):
    """
    Called when a new PlugSession is created (known NFC scan).
    Reads device timer settings and arms all three stages.
    """
    _do_schedule(session_id)


def cancel_escalation(session_id: str):
    """
    Cancel all pending timers for this session.
    Call on: NFC removed, user cutoff, or before rescheduling.
    """
    sid = str(session_id)
    with _timers_lock:
        if sid in _timers:
            for t in _timers[sid].values():
                t.cancel()
            del _timers[sid]
            logger.debug(f"Escalation cancelled for session {sid}")


def reset_escalation(session_id: str):
    """
    Cancel all timers and reschedule from zero.
    Called when user responds "Yes, still using it".
    """
    cancel_escalation(session_id)
    _do_schedule(session_id)


# ── Internal ──────────────────────────────────────────────────────────────────

def _do_schedule(session_id: str):
    """Load session from DB and arm timers based on device settings."""
    close_old_connections()
    print(f"[ESCALATION] _do_schedule called for session {session_id}")
    try:
        from device.models import PlugSession

        session = (
            PlugSession.objects
            .select_related('device', 'plug', 'plug__house')
            .filter(id=session_id, is_active=True)
            .first()
        )
        if not session:
            logger.debug(f"_do_schedule: session {session_id} not active, skip")
            return

        device = session.device
        if not device:
            return

        sid = str(session.id)
        plug_id = str(session.plug.id)
        house_id = str(session.plug.house.id)

        timers = {}

        if device.until_notify_minutes:
            t = threading.Timer(
                device.until_notify_minutes * 60,
                _fire_stage,
                args=[plug_id, sid, house_id, 'notify'],
            )
            t.daemon = True
            t.start()
            timers['notify'] = t

        if device.until_alert_minutes:
            t = threading.Timer(
                device.until_alert_minutes * 60,
                _fire_stage,
                args=[plug_id, sid, house_id, 'alert'],
            )
            t.daemon = True
            t.start()
            timers['alert'] = t

        if device.until_cutoff_minutes:
            t = threading.Timer(
                device.until_cutoff_minutes * 60,
                _fire_stage,
                args=[plug_id, sid, house_id, 'cutoff'],
            )
            t.daemon = True
            t.start()
            timers['cutoff'] = t

        with _timers_lock:
            _timers[sid] = timers

        print(f"[ESCALATION] Armed for session {sid} | notify={device.until_notify_minutes}m alert={device.until_alert_minutes}m cutoff={device.until_cutoff_minutes}m")
        logger.info(
            f"Escalation armed for session {sid} | "
            f"notify={device.until_notify_minutes}m "
            f"alert={device.until_alert_minutes}m "
            f"cutoff={device.until_cutoff_minutes}m"
        )

    except Exception as e:
        print(f"[ESCALATION] _do_schedule error: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"_do_schedule error: {e}", exc_info=True)
    finally:
        close_old_connections()


def _fire_stage(plug_id: str, session_id: str, house_id: str, level: str):
    """Timer callback — checks session is still active then acts."""
    close_old_connections()
    print(f"[ESCALATION] Timer fired: level={level} session={session_id}")
    try:
        from device.models import PlugSession

        session = (
            PlugSession.objects
            .select_related('device', 'plug')
            .filter(id=session_id, is_active=True)
            .first()
        )
        if not session:
            logger.debug(f"_fire_stage({level}): session {session_id} gone, skip")
            return

        if level == 'cutoff':
            _handle_cutoff(session, house_id)
        else:
            # notify or alert — broadcast, user decides
            _broadcast_escalation(house_id, session, level)

    except Exception as e:
        print(f"[ESCALATION] _fire_stage({level}) error: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"_fire_stage({level}) error: {e}", exc_info=True)
    finally:
        close_old_connections()


def _handle_cutoff(session, house_id: str):
    """Auto power-off: fire MQTT, end session, broadcast cutoff."""
    from alert.engine import execute_auto_off, end_session, broadcast_session_ended

    print(f"[ESCALATION] _handle_cutoff starting for session {session.id}")
    plug_code = session.plug.plug_code
    print(f"[ESCALATION] Plug code: {plug_code}")

    try:
        execute_auto_off(session.plug)
        print(f"[ESCALATION] execute_auto_off returned successfully")
    except Exception as e:
        print(f"[ESCALATION] execute_auto_off FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

    try:
        end_session(session)
        print(f"[ESCALATION] end_session returned successfully")
    except Exception as e:
        print(f"[ESCALATION] end_session FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

    device_name = session.device.name if session.device else ''
    broadcast_session_ended(
        house_id=house_id,
        session_id=str(session.id),
        plug_id=str(session.plug.id),
        plug_name=session.plug.name,
        device_name=device_name,
        reason='auto_cutoff',
    )

    # Also send a calm cutoff broadcast so the frontend can update the modal
    _broadcast_escalation(house_id, session, 'cutoff')

    # Cancel any remaining notify/alert timers (they shouldn't exist, but be safe)
    cancel_escalation(str(session.id))

    print(f"[ESCALATION] Auto cutoff executed for session {session.id}")
    logger.info(f"Auto cutoff executed for session {session.id}")


def _broadcast_escalation(house_id: str, session, level: str):
    """Send escalation event to the house WebSocket group."""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    device = session.device
    plug = session.plug

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"house_{house_id}",
        {
            "type": "house.event",
            "event": f"escalation_{level}",
            "session_id": str(session.id),
            "plug_id": str(plug.id),
            "plug_name": plug.name,
            "device_id": str(device.id) if device else None,
            "device_name": device.name if device else "Unknown device",
            "notify_minutes": device.until_notify_minutes if device else None,
            "alert_minutes": device.until_alert_minutes if device else None,
            "cutoff_minutes": device.until_cutoff_minutes if device else None,
            "house_id": str(house_id),
        },
    )
    print(f"[ESCALATION] Broadcast escalation_{level} for session {session.id}")
    logger.info(f"Broadcast escalation_{level} for session {session.id}")
