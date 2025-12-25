from __future__ import annotations

import json
import os
import urllib.parse
from typing import Any

from . import filters, http_client, request_builders, validators

LOG_PATH_DEFAULT = "/tmp/sharepoint_list.debug.ndjson"


def _get_debug_log_path() -> str:
    return os.getenv("SHAREPOINT_LIST_DEBUG_LOG_PATH", LOG_PATH_DEFAULT)


class GraphError(http_client.GraphAPIError):
    """Raised when Graph API returns an error response. (Legacy alias)"""


def _send_request(
    spec: request_builders.RequestSpec,
    access_token: str,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Send request with retry logic. Wrapper for http_client."""
    if _is_debug_log_enabled():
        safe_headers = {
            k: v
            for k, v in (extra_headers or {}).items()
            if k.lower() != "authorization"
        }
        _log_debug(
            location="operations.py:_send_request",
            message="request",
            data={
                "url": spec.url,
                "params": spec.params,
                "json": spec.json is not None,
                "headers": safe_headers,
            },
        )

    try:
        return http_client.send_request_with_retry(
            spec=spec,
            access_token=access_token,
            extra_headers=extra_headers,
        )
    except http_client.GraphAPIError as e:
        if _is_debug_log_enabled():
            _log_debug(
                location="operations.py:_send_request",
                message="error",
                data={
                    "status": e.status_code,
                    "text": (e.response_text or "")[:200],
                    "error_type": type(e).__name__,
                },
            )
        raise


def _is_debug_log_enabled() -> bool:
    val = os.getenv("SHAREPOINT_LIST_DEBUG_LOG", "").lower()
    return val in {"1", "true", "yes", "on"}


def _log_debug(location: str, message: str, data: dict[str, Any]) -> None:
    if not _is_debug_log_enabled():
        return
    try:
        log_payload = {
            "sessionId": "debug-session",
            "runId": os.getenv("SHAREPOINT_LIST_DEBUG_RUN_ID", "run1"),
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(__import__("time").time() * 1000),
        }
        with open(_get_debug_log_path(), "a") as f:
            f.write(json.dumps(log_payload, ensure_ascii=False) + "\n")
    except Exception:
        # fail silently to avoid impacting main flow
        pass


def resolve_site_id(access_token: str, site_identifier: str) -> str:
    """
    Accepts site_identifier that may be:
    - URL (starts with http)
    - site ID (host,siteId,webId) or GUID-like token
    - site path token (best-effort; treated as site ID)
    """
    if site_identifier.startswith("http"):
        spec = request_builders.build_site_get_by_path_request(site_identifier)
        data = _send_request(spec, access_token)
        resolved = data.get("id")
        if not resolved:
            raise GraphError("Failed to resolve site_id from site_url")
        return resolved

    # If identifier already looks like site ID (contains commas or GUID), use as-is
    if "," in site_identifier or validators.is_guid(site_identifier):
        return site_identifier

    # Fallback: treat as ID token (best-effort)
    return site_identifier


def resolve_list_id(
    access_token: str, site_id: str, list_identifier: str
) -> str:
    if validators.is_guid(list_identifier):
        return list_identifier

    # Try filter by displayName
    filter_req = request_builders.build_list_filter_request(
        site_id=site_id, list_name=list_identifier
    )
    filter_data = _send_request(filter_req, access_token)
    values = filter_data.get("value") or []
    if len(values) == 1:
        found_id = values[0].get("id")
        if found_id:
            return found_id

    # Fallback enumerate
    enum_req = request_builders.build_list_enumerate_request(site_id=site_id)
    enum_data = _send_request(enum_req, access_token)
    for item in enum_data.get("value", []):
        if item.get("displayName") == list_identifier:
            found_id = item.get("id")
            if found_id:
                return found_id

    raise GraphError(f"List '{list_identifier}' not found in site '{site_id}'")


def create_item(
    access_token: str, target: validators.TargetSpec, fields: dict[str, Any]
) -> dict[str, Any]:
    site_id = resolve_site_id(access_token, target.site_identifier)
    list_id = resolve_list_id(access_token, site_id, target.list_identifier)
    display_to_name, name_set, _ = _get_column_maps(access_token, site_id, list_id)
    mapped_fields = map_fields_to_internal(fields, display_to_name, name_set)
    spec = request_builders.build_create_item_request(
        site_id=site_id, list_id=list_id, fields=mapped_fields
    )
    return _send_request(spec, access_token)


def update_item(
    access_token: str,
    target: validators.TargetSpec,
    item_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    site_id = resolve_site_id(access_token, target.site_identifier)
    list_id = resolve_list_id(access_token, site_id, target.list_identifier)
    display_to_name, name_set, _ = _get_column_maps(access_token, site_id, list_id)
    mapped_fields = map_fields_to_internal(fields, display_to_name, name_set)
    spec = request_builders.build_update_item_request(
        site_id=site_id, list_id=list_id, item_id=item_id, fields=mapped_fields
    )
    return _send_request(spec, access_token)


def get_item(
    access_token: str,
    target: validators.TargetSpec,
    item_id: str,
    select_fields: list[str] | None = None,
) -> dict[str, Any]:
    site_id = resolve_site_id(access_token, target.site_identifier)
    list_id = resolve_list_id(access_token, site_id, target.list_identifier)
    select_fields = resolve_select_fields_for_list(
        access_token=access_token,
        site_id=site_id,
        list_id=list_id,
        select_fields=select_fields,
    )
    spec = request_builders.build_get_item_request(
        site_id=site_id,
        list_id=list_id,
        item_id=item_id,
        select_fields=select_fields,
    )
    return _send_request(spec, access_token)


def parse_select_fields(select_fields: str | None) -> list[str] | None:
    if not select_fields:
        return None
    text = select_fields.strip()
    # select_fields が '"Title"' のように全体をクォートして渡された場合に備え、
    # 外側クォートを除去
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        text = text[1:-1]
    parts = []
    for raw in text.split(","):
        cleaned = raw.strip().strip('"').strip("'")
        if cleaned:
            parts.append(cleaned)
    return parts or None


def _get_column_maps(
    access_token: str, site_id: str, list_id: str
) -> tuple[dict[str, str], set[str], dict[str, Any]]:
    """
    Fetch columns once and return (display_to_name, name_set, raw_columns_data).
    """
    columns_spec = request_builders.build_list_columns_request(
        site_id=site_id, list_id=list_id
    )
    columns_data = _send_request(columns_spec, access_token)
    display_to_name: dict[str, str] = {}
    name_set: set[str] = set()
    for col in columns_data.get("value", []):
        display = col.get("displayName")
        name = col.get("name")
        if isinstance(name, str):
            name_set.add(name.lower())
        if isinstance(display, str) and isinstance(name, str):
            display_to_name[display.lower()] = name
    return display_to_name, name_set, columns_data


def _map_field_name(
    raw: str, display_to_name: dict[str, str], name_set: set[str]
) -> str:
    lowered = raw.lower()
    if lowered in name_set:
        return raw
    if lowered in display_to_name:
        return display_to_name[lowered]
    return raw


def map_fields_to_internal(
    fields: dict[str, Any],
    display_to_name: dict[str, str],
    name_set: set[str],
) -> dict[str, Any]:
    """
    Map field keys that may be given as displayName to internal column names.
    Unknown keys are kept as-is.
    """
    mapped: dict[str, Any] = {}
    for key, value in fields.items():
        mapped_key = _map_field_name(str(key), display_to_name, name_set)
        mapped[mapped_key] = value
    return mapped


def resolve_select_fields_for_list(
    access_token: str,
    site_id: str,
    list_id: str,
    select_fields: list[str] | None,
    *,
    display_to_name: dict[str, str] | None = None,
    name_set: set[str] | None = None,
    columns_data: dict[str, Any] | None = None,
) -> list[str] | None:
    """
    Map select_fields that may be given as displayName (e.g., 日本語の列表示名)
    to internal column names. If a field already matches an internal name, it is kept.
    """
    if not select_fields:
        return None

    if display_to_name is None or name_set is None:
        display_to_name, name_set, _ = _get_column_maps(
            access_token, site_id, list_id
        )

    resolved: list[str] = []
    for raw in select_fields:
        lower = raw.lower()
        if lower in name_set:
            resolved.append(raw)
        elif lower in display_to_name:
            resolved.append(display_to_name[lower])
        else:
            resolved.append(raw)
    return resolved or None


def get_choice_field_info(
    access_token: str,
    site_identifier: str,
    list_identifier: str,
    field_identifier: str,
) -> dict[str, Any]:
    """
    Return choice field metadata and choices.
    - field_identifier: internal name or display name (case-insensitive)
    """
    site_id = resolve_site_id(access_token, site_identifier)
    list_id = resolve_list_id(access_token, site_id, list_identifier)

    columns_spec = request_builders.build_list_columns_request(
        site_id=site_id, list_id=list_id
    )
    columns_data = _send_request(columns_spec, access_token)

    if _is_debug_log_enabled():
        # region agent log
        try:
            log_payload = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H1",
                "location": "operations.py:get_choice_field_info",
                "message": "columns fetched",
                "data": {
                    "field_identifier": field_identifier,
                    "columns_count": (
                        len(columns_data.get("value", []))
                        if isinstance(columns_data, dict)
                        else None
                    ),
                    "names": [
                        c.get("name")
                        for c in (
                            columns_data.get("value", [])
                            if isinstance(columns_data, dict)
                            else []
                        )
                    ],
                    "displayNames": [
                        c.get("displayName")
                        for c in (
                            columns_data.get("value", [])
                            if isinstance(columns_data, dict)
                            else []
                        )
                    ],
                },
                "timestamp": int(__import__("time").time() * 1000),
            }
            with open(_get_debug_log_path(), "a") as f:
                f.write(json.dumps(log_payload, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # endregion

    target_col = None
    lowered = field_identifier.lower()
    for col in columns_data.get("value", []):
        name = col.get("name")
        display = col.get("displayName")
        if isinstance(name, str) and name.lower() == lowered:
            target_col = col
            break
        if isinstance(display, str) and display.lower() == lowered:
            target_col = col
            break

    if not target_col:
        raise GraphError(
            f"Field '{field_identifier}' not found in list '{list_identifier}'"
        )

    if _is_debug_log_enabled():
        # region agent log
        try:
            log_payload = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H2",
                "location": "operations.py:get_choice_field_info",
                "message": "column matched",
                "data": {
                    "field_identifier": field_identifier,
                    "name": target_col.get("name"),
                    "displayName": target_col.get("displayName"),
                    "columnType": target_col.get("columnType"),
                    "choice_keys": list(
                        (target_col.get("choice") or {}).keys()
                    ),
                },
                "timestamp": int(__import__("time").time() * 1000),
            }
            with open(_get_debug_log_path(), "a") as f:
                f.write(json.dumps(log_payload, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # endregion

    column_type = target_col.get("columnType")
    choice = target_col.get("choice") or {}
    is_choice = (column_type == "choice") or bool(choice)
    if not is_choice:
        err_msg = (
            f"Field '{field_identifier}' is not a choice column "
            f"(columnType={column_type})"
        )
        raise GraphError(err_msg)

    if _is_debug_log_enabled():
        # region agent log
        try:
            log_payload = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H3",
                "location": "operations.py:get_choice_field_info",
                "message": "choice payload",
                "data": {
                    "displayName": target_col.get("displayName"),
                    "name": target_col.get("name"),
                    "allowMultipleSelections": choice.get(
                        "allowMultipleSelections"
                    ),
                    "defaultValue": choice.get("defaultValue"),
                    "choices_len": len(choice.get("choices") or []),
                },
                "timestamp": int(__import__("time").time() * 1000),
            }
            with open(_get_debug_log_path(), "a") as f:
                f.write(json.dumps(log_payload, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # endregion

    return {
        "displayName": target_col.get("displayName"),
        "name": target_col.get("name"),
        "choices": choice.get("choices"),
        "allowMultipleSelections": choice.get("allowMultipleSelections"),
        "defaultValue": choice.get("defaultValue"),
    }


def list_items(
    access_token: str,
    target: validators.TargetSpec,
    select_fields: str | None,
    page_size: int = 20,
    page_token: str | None = None,
    filters_raw: str | None = None,
) -> dict[str, Any]:
    site_id = resolve_site_id(access_token, target.site_identifier)
    list_id = resolve_list_id(access_token, site_id, target.list_identifier)

    need_columns = bool(select_fields) or bool(filters_raw)
    display_to_name: dict[str, str] = {}
    name_set: set[str] = set()
    columns_data: dict[str, Any] | None = None
    if need_columns:
        display_to_name, name_set, columns_data = _get_column_maps(
            access_token, site_id, list_id
        )

    # resolve select fields (displayName or internal)
    parsed_select = parse_select_fields(select_fields)
    mapped_select = resolve_select_fields_for_list(
        access_token=access_token,
        site_id=site_id,
        list_id=list_id,
        select_fields=parsed_select,
        display_to_name=display_to_name or None,
        name_set=name_set or None,
        columns_data=columns_data,
    )

    clauses: list[str] = []

    uses_fields_clause = False

    # multiple filters
    if filters_raw:
        parsed_filters = filters.parse_filters(filters_raw)
        for cond in parsed_filters:
            mapped = _map_field_name(cond.field, display_to_name, name_set)
            field_ref = mapped
            if mapped != "createdDateTime":
                field_ref = f"fields/{mapped}"
                uses_fields_clause = True
            fragment = filters.build_filter_fragment(cond, field_ref)
            clauses.append(fragment)

    filter_expr = " and ".join(clauses) if clauses else None

    top = max(1, min(page_size, 100))

    prefer_added = False
    req = request_builders.build_list_items_request(
        site_id=site_id,
        list_id=list_id,
        top=top,
        skiptoken=page_token,
        filter_expr=filter_expr,
        select_fields=mapped_select,
        orderby="createdDateTime desc",
    )
    # SharePoint lists may reject filtering on non-indexed fields
    # unless Prefer header is provided.
    # Provide Prefer header as a best-effort mitigation.
    extra_headers = None
    if filter_expr and (uses_fields_clause or "fields/" in filter_expr):
        extra_headers = {"Prefer": "HonorNonIndexedQueriesWarning=true"}
        prefer_added = True

    if _is_debug_log_enabled():
        _log_debug(
            location="operations.py:list_items",
            message="request_args",
            data={
                "filters_raw": filters_raw,
                "filter_expr": filter_expr,
                "orderby": "createdDateTime desc",
                "page_size": top,
                "page_token": page_token,
                "prefer_added": prefer_added,
            },
        )

    data = _send_request(req, access_token, extra_headers=extra_headers)

    next_token = None
    next_link = data.get("@odata.nextLink") if isinstance(data, dict) else None
    if isinstance(next_link, str):
        parsed = urllib.parse.urlparse(next_link)
        qs = urllib.parse.parse_qs(parsed.query)
        tokens = qs.get("$skiptoken") or qs.get("%24skiptoken")
        if tokens:
            next_token = tokens[0]

    return {
        "items": data.get("value", []) if isinstance(data, dict) else [],
        "next_page_token": next_token,
    }
