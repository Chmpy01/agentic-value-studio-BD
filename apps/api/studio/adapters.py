"""Read-only fixture adapters. No network calls and no control writes."""
from __future__ import annotations

from studio.config import DENIED_ACTIONS


class PolicyDenied(PermissionError):
    pass


class ToolAdapter:
    """Deny-by-default tool boundary. Subclasses may read fixtures only."""

    name = "base"
    product_family = "unspecified"
    access = "read-only"
    entitlement = "Not connected. No customer credential is configured."

    def read(self, intent: dict) -> dict:
        return {
            "adapter": self.name,
            "productFamily": self.product_family,
            "access": self.access,
            "entitlement": self.entitlement,
            "provenance": "synthetic",
            "readings": [],
        }

    def invoke(self, action: str, payload: dict | None = None) -> dict:
        if action in DENIED_ACTIONS or action.endswith(".write"):
            raise PolicyDenied(f"denied action {action}")
        raise PolicyDenied(f"action {action} is not on the allow list")


def _match(intent: dict, needles: tuple[str, ...]) -> list[dict]:
    rows = []
    for item in intent["evidence"]["snapshots"]:
        source = item.get("source", "").lower()
        if any(needle in source for needle in needles):
            rows.append(dict(item))
    return rows


class SpacesOccupancyAdapter(ToolAdapter):
    name = "spaces-occupancy"
    product_family = "Cisco Spaces-style occupancy (synthetic stand-in)"

    def read(self, intent: dict) -> dict:
        receipt = super().read(intent)
        receipt["readings"] = _match(intent, ("space",))
        receipt["assumption"] = "Occupancy is a synthetic aggregate, not a live Spaces tenant."
        return receipt


class WebexRoomsAdapter(ToolAdapter):
    name = "webex-rooms"
    product_family = "Webex-style room and meeting usage (synthetic stand-in)"

    def read(self, intent: dict) -> dict:
        receipt = super().read(intent)
        receipt["readings"] = _match(intent, ("book", "webex", "meeting"))
        receipt["assumption"] = "No Webex API is called. Booking figures come from the scenario fixture."
        return receipt


class BmsHistorianAdapter(ToolAdapter):
    name = "bms-historian"
    product_family = "BMS / meter historian (synthetic stand-in)"

    def read(self, intent: dict) -> dict:
        receipt = super().read(intent)
        receipt["readings"] = _match(intent, ("bms", "meter", "hvac", "temperature"))
        receipt["assumption"] = "Historian values are synthetic. This adapter cannot write setpoints."
        return receipt


class SplunkEventsAdapter(ToolAdapter):
    name = "splunk-events"
    product_family = "Splunk-style operational events (synthetic stand-in)"

    def read(self, intent: dict) -> dict:
        receipt = super().read(intent)
        receipt["readings"] = _match(intent, ("splunk",))
        if not receipt["readings"]:
            receipt["note"] = "This pack has no Splunk-labelled fixture. The adapter is not connected."
        return receipt


class FmTicketAdapter(ToolAdapter):
    name = "fm-ticket"
    product_family = "Facilities work-order desk (local simulation)"
    access = "simulated-draft"

    def read(self, intent: dict) -> dict:
        receipt = super().read(intent)
        receipt["readings"] = []
        receipt["note"] = "No facilities system is connected. Drafts stay in the local audit log."
        return receipt

    def invoke(self, action: str, payload: dict | None = None) -> dict:
        if action in DENIED_ACTIONS or (action.endswith(".write") and action != "draft_work_order"):
            raise PolicyDenied(f"denied action {action}")
        if action != "draft_work_order":
            raise PolicyDenied(f"action {action} is not on the allow list")
        payload = payload or {}
        if payload.get("approved") is not True:
            raise PolicyDenied("draft_work_order requires a recorded approval")
        if payload.get("consumed") is True:
            raise PolicyDenied("action key already used")
        return {
            "adapter": self.name,
            "ticketType": "SIMULATED_WORK_ORDER",
            "status": "DRAFTED_ONLY",
            "externalSystemWritten": False,
            "idempotencyKey": payload.get("idempotencyKey"),
            "summary": payload.get("summary"),
        }


READ_ADAPTERS = (
    SpacesOccupancyAdapter(),
    WebexRoomsAdapter(),
    BmsHistorianAdapter(),
    SplunkEventsAdapter(),
    FmTicketAdapter(),
)


def collect_readings(intent: dict) -> list[dict]:
    return [adapter.read(intent) for adapter in READ_ADAPTERS]


def adapter_for(action: str) -> ToolAdapter:
    if action == "draft_work_order":
        return FmTicketAdapter()
    if action in DENIED_ACTIONS:
        return BmsHistorianAdapter()
    raise PolicyDenied(f"no adapter for {action}")
