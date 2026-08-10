#!/usr/bin/env python3
"""Validate a permission model before implementing it.

Reads the machine-readable form of a permission matrix (see
assets/templates/permission-model.example.json) and reports the mistakes that
are easy to make in a large matrix and expensive to find later:

  - buttons granted to a role that lacks the parent menu (unreachable button)
  - write permissions granted without the matching read (can edit, cannot see)
  - permissions no role can reach, and roles with nothing granted
  - typos in grants, with a suggestion for the intended code
  - permissions no plan includes (unreachable by every tenant)
  - malformed codes, broken menu-tree parentage, and cycles
  - type rules: menus need routes, buttons must not have them, external links

Usage
-----
    python validate_permission_model.py permission-model.json
    python validate_permission_model.py model.json --strict   # warnings fail too
    python validate_permission_model.py model.json --json     # machine output

Exit codes: 0 clean, 1 errors found (or warnings with --strict), 2 bad input.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*(:[a-z0-9][a-z0-9-]*)*$")
VALID_TYPES = {"dir", "menu", "button"}
VALID_SCOPES = {"ALL", "CUSTOM", "DEPT_AND_BELOW", "DEPT", "SELF"}
VALID_FIELD_ACCESS = {"read", "write", "masked", "none"}

# Used to infer read/write intent when a permission omits an explicit "action".
READ_ACTIONS = {
    "list", "view", "read", "get", "query", "detail", "page", "search",
    "export", "download", "preview", "print", "stat", "report",
}
WRITE_ACTIONS = {
    "create", "add", "new", "edit", "update", "modify", "delete", "remove",
    "import", "upload", "audit", "approve", "reject", "assign", "grant",
    "revoke", "reset", "reset-password", "enable", "disable", "transfer",
    "operate", "publish", "unpublish", "submit", "cancel", "refund", "share",
    "start", "stop", "manage", "config", "sync", "send",
}


@dataclass
class Finding:
    level: str  # "error" | "warning"
    code: str
    message: str
    hint: str = ""

    def sort_key(self) -> tuple:
        return (0 if self.level == "error" else 1, self.code, self.message)


@dataclass
class Model:
    permissions: list[dict] = field(default_factory=list)
    roles: list[dict] = field(default_factory=list)
    plans: list[dict] = field(default_factory=list)
    mutex: list[list[str]] = field(default_factory=list)
    field_rules: list[dict] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def matches(pattern: str, code: str) -> bool:
    """Grant-side wildcard match.

    '*' matches everything. 'prefix:*' matches 'prefix' and everything beneath
    it. Anything else is an exact match. Wildcards are only ever valid in
    grants and plan ceilings, never in a runtime permission check.
    """
    if pattern == "*":
        return True
    if pattern.endswith(":*"):
        prefix = pattern[:-2]
        return code == prefix or code.startswith(prefix + ":")
    return pattern == code


def expand(patterns: list[str], all_codes: list[str]) -> set[str]:
    return {c for c in all_codes for p in patterns if matches(p, c)}


def action_kind(perm: dict) -> str:
    """Return 'read', 'write', or 'unknown' for a permission node."""
    explicit = (perm.get("action") or "").strip().lower()
    if explicit in {"read", "write"}:
        return explicit
    last = perm["code"].rsplit(":", 1)[-1]
    if last in READ_ACTIONS:
        return "read"
    if last in WRITE_ACTIONS:
        return "write"
    return "unknown"


def suggest(bad: str, candidates: list[str]) -> str:
    close = difflib.get_close_matches(bad, candidates, n=1, cutoff=0.75)
    return f"did you mean '{close[0]}'?" if close else ""


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #

def check_permissions(model: Model, out: list[Finding]) -> dict[str, dict]:
    """Validate the permission tree. Returns the code -> permission index."""
    index: dict[str, dict] = {}

    for i, p in enumerate(model.permissions):
        code = p.get("code")
        if not code:
            out.append(Finding("error", "E000", f"permission #{i} has no 'code'"))
            continue
        if code in index:
            out.append(Finding("error", "E001", f"duplicate permission code '{code}'"))
            continue
        if not CODE_PATTERN.match(code):
            out.append(Finding(
                "error", "E002", f"malformed permission code '{code}'",
                "expected lowercase module:resource:action, segments of [a-z0-9-]",
            ))
        ptype = p.get("type")
        if ptype not in VALID_TYPES:
            out.append(Finding(
                "error", "E005",
                f"permission '{code}' has invalid type {ptype!r}",
                f"expected one of {sorted(VALID_TYPES)}",
            ))
        index[code] = p

    for code, p in index.items():
        parent = p.get("parent")
        ptype = p.get("type")

        # parentage
        if parent is not None:
            if parent not in index:
                out.append(Finding(
                    "error", "E003", f"permission '{code}' has unknown parent '{parent}'",
                    suggest(parent, list(index)),
                ))
            else:
                parent_type = index[parent].get("type")
                if ptype == "button" and parent_type != "menu":
                    out.append(Finding(
                        "error", "E006",
                        f"button '{code}' has parent '{parent}' of type '{parent_type}'",
                        "buttons must hang off a menu, otherwise the page has no entry to guard",
                    ))
                if ptype in {"dir", "menu"} and parent_type != "dir":
                    out.append(Finding(
                        "error", "E007",
                        f"{ptype} '{code}' has parent '{parent}' of type '{parent_type}'",
                        "directories and menus nest under a directory",
                    ))
                if not code.startswith(parent + ":"):
                    out.append(Finding(
                        "error", "E015",
                        f"code '{code}' does not extend its parent code '{parent}'",
                        "a child's code must be the parent's code plus ':segment', "
                        "so the code path and the tree describe the same structure",
                    ))
                elif code.count(":") != parent.count(":") + 1:
                    out.append(Finding(
                        "warning", "W009",
                        f"code '{code}' skips a level below parent '{parent}'",
                    ))
        elif ptype == "button":
            out.append(Finding(
                "error", "E006", f"button '{code}' has no parent menu",
            ))

        # type-specific fields
        if ptype == "menu" and not p.get("route_path") and not p.get("is_external"):
            out.append(Finding(
                "error", "E008", f"menu '{code}' has no route_path",
                "a menu is a real page; without a route there is nothing to open",
            ))
        if ptype == "button" and (p.get("route_path") or p.get("component")):
            out.append(Finding(
                "error", "E009",
                f"button '{code}' defines route_path/component",
                "buttons are operations inside a page and carry only a code",
            ))
        if ptype == "dir" and p.get("route_path") and not p.get("is_external"):
            out.append(Finding(
                "warning", "W010",
                f"directory '{code}' defines a route_path but is not an external link",
            ))
        if p.get("is_external"):
            rp = p.get("route_path") or ""
            if not rp.startswith(("http://", "https://")):
                out.append(Finding(
                    "error", "E010",
                    f"external permission '{code}' has route_path '{rp}'",
                    "external links must start with http:// or https://",
                ))

    # cycles
    for code in index:
        seen, cur = set(), code
        while cur is not None:
            if cur in seen:
                out.append(Finding("error", "E004", f"parent cycle involving '{code}'"))
                break
            seen.add(cur)
            nxt = index.get(cur, {}).get("parent")
            cur = nxt if nxt in index else None

    # menus with no operations under them
    for code, p in index.items():
        if p.get("type") != "menu":
            continue
        if not any(c.get("parent") == code for c in index.values()):
            out.append(Finding(
                "warning", "W006", f"menu '{code}' has no button permissions under it",
                "page access exists but no operation is separately controllable",
            ))

    return index


def check_roles(model: Model, index: dict[str, dict], out: list[Finding]) -> dict[str, set[str]]:
    """Validate roles and their grants. Returns role code -> resolved codes."""
    all_codes = list(index)
    resolved: dict[str, set[str]] = {}
    seen_codes: set[str] = set()

    if model.roles and not any(r.get("builtin") for r in model.roles):
        out.append(Finding(
            "warning", "W007", "no role is marked builtin",
            "ship built-in roles so most tenants never need to configure one",
        ))

    for i, r in enumerate(model.roles):
        rcode = r.get("code")
        if not rcode:
            out.append(Finding("error", "E000", f"role #{i} has no 'code'"))
            continue
        if rcode in seen_codes:
            out.append(Finding("error", "E016", f"duplicate role code '{rcode}'"))
            continue
        seen_codes.add(rcode)

        grants = r.get("permissions") or []
        for g in grants:
            if not any(matches(g, c) for c in all_codes):
                out.append(Finding(
                    "error", "E011",
                    f"role '{rcode}' grants '{g}', which matches no permission",
                    suggest(g, all_codes) or "a check against a nonexistent code fails closed forever",
                ))
            elif ("*" in g) and not r.get("builtin"):
                out.append(Finding(
                    "warning", "W008",
                    f"custom role '{rcode}' holds wildcard grant '{g}'",
                    "wildcards silently absorb every future permission under that "
                    "prefix; fine for built-in admins, surprising for customer roles",
                ))

        got = expand(grants, all_codes)
        resolved[rcode] = got

        if not got:
            out.append(Finding("warning", "W002", f"role '{rcode}' has no permissions"))

        # data scope
        for key in ("data_scope", "write_scope"):
            scope = r.get(key)
            if scope is None:
                continue
            if scope not in VALID_SCOPES:
                out.append(Finding(
                    "error", "E013",
                    f"role '{rcode}' has invalid {key} {scope!r}",
                    f"expected one of {sorted(VALID_SCOPES)}",
                ))
            elif scope == "CUSTOM" and not r.get("depts"):
                out.append(Finding(
                    "error", "E014",
                    f"role '{rcode}' uses {key}=CUSTOM but lists no departments",
                    "an empty custom scope must mean zero rows, not no filter -- "
                    "make the intent explicit here",
                ))

        # button granted without its parent menu
        for code in sorted(got):
            p = index[code]
            if p.get("type") != "button":
                continue
            parent = p.get("parent")
            if parent and parent not in got:
                out.append(Finding(
                    "warning", "W004",
                    f"role '{rcode}' has button '{code}' but not its menu '{parent}'",
                    "the page is unreachable, so the button can never be clicked",
                ))

        # write granted without a read on the same menu
        for code in sorted(got):
            p = index[code]
            if p.get("type") != "button" or action_kind(p) != "write":
                continue
            parent = p.get("parent")
            siblings = [
                c for c in index.values()
                if c.get("parent") == parent and action_kind(c) == "read"
            ]
            if not siblings:
                continue  # nothing readable defined on this menu; not this role's problem
            if not any(s["code"] in got for s in siblings):
                out.append(Finding(
                    "warning", "W003",
                    f"role '{rcode}' can write '{code}' but has no read permission on '{parent}'",
                    "can modify what it cannot see -- usually a missing cell in the matrix",
                ))

    # mutex
    for group in model.mutex:
        if not isinstance(group, list) or len(group) < 2:
            out.append(Finding("error", "E012", f"mutex group {group!r} needs at least two roles"))
            continue
        if len(set(group)) != len(group):
            out.append(Finding("error", "E012", f"mutex group {group!r} repeats a role"))
        for rc in group:
            if rc not in seen_codes:
                out.append(Finding(
                    "error", "E012", f"mutex group references unknown role '{rc}'",
                    suggest(rc, sorted(seen_codes)),
                ))

    # permissions nobody can reach
    granted_anywhere: set[str] = set().union(*resolved.values()) if resolved else set()
    for code in index:
        if code not in granted_anywhere:
            out.append(Finding(
                "warning", "W001", f"permission '{code}' is granted to no role",
                "either a role is missing a cell, or the permission is dead weight",
            ))

    return resolved


def check_plans(model: Model, index: dict[str, dict], out: list[Finding]) -> None:
    if not model.plans:
        return
    all_codes = list(index)
    covered: set[str] = set()

    for i, plan in enumerate(model.plans):
        pcode = plan.get("code") or f"#{i}"
        grants = plan.get("permissions") or []
        for g in grants:
            if not any(matches(g, c) for c in all_codes):
                out.append(Finding(
                    "error", "E017",
                    f"plan '{pcode}' includes '{g}', which matches no permission",
                    suggest(g, all_codes),
                ))
        covered |= expand(grants, all_codes)

    for code in index:
        if code not in covered:
            out.append(Finding(
                "warning", "W005", f"permission '{code}' is in no plan",
                "capped for every tenant, so no customer can ever use it",
            ))


def check_field_rules(model: Model, index: dict[str, dict], role_codes: set[str],
                      out: list[Finding]) -> None:
    for i, rule in enumerate(model.field_rules):
        where = f"field rule #{i}"
        role = rule.get("role")
        if role not in role_codes:
            out.append(Finding(
                "error", "E018", f"{where} references unknown role '{role}'",
                suggest(str(role), sorted(role_codes)),
            ))
        resource = rule.get("resource")
        if resource not in index:
            out.append(Finding(
                "warning", "W011", f"{where} references resource '{resource}' "
                "which is not a permission code",
            ))
        access = rule.get("access")
        if access not in VALID_FIELD_ACCESS:
            out.append(Finding(
                "error", "E019", f"{where} has invalid access {access!r}",
                f"expected one of {sorted(VALID_FIELD_ACCESS)}",
            ))
        if not rule.get("field"):
            out.append(Finding("error", "E019", f"{where} has no 'field'"))


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #

def validate(raw: dict) -> tuple[list[Finding], dict]:
    model = Model(
        permissions=raw.get("permissions") or [],
        roles=raw.get("roles") or [],
        plans=raw.get("plans") or [],
        mutex=raw.get("mutex") or [],
        field_rules=raw.get("field_rules") or [],
    )
    out: list[Finding] = []

    if not model.permissions:
        out.append(Finding("error", "E000", "model defines no permissions"))
        return out, {"permissions": 0, "roles": 0, "plans": 0}

    index = check_permissions(model, out)
    resolved = check_roles(model, index, out)
    check_plans(model, index, out)
    check_field_rules(model, index, set(resolved), out)

    stats = {
        "permissions": len(index),
        "roles": len(resolved),
        "plans": len(model.plans),
        "field_rules": len(model.field_rules),
    }
    return out, stats


def render(path: Path, findings: list[Finding], stats: dict) -> None:
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]

    print(f"\n{path}")

    for label, group in (("ERRORS", errors), ("WARNINGS", warnings)):
        if not group:
            continue
        print(f"\n{label} ({len(group)})")
        for f in sorted(group, key=Finding.sort_key):
            print(f"  {f.code}  {f.message}")
            if f.hint:
                print(f"        -> {f.hint}")

    summary = ", ".join(f"{v} {k}" for k, v in stats.items() if v)
    print(f"\n{summary} -- {len(errors)} error(s), {len(warnings)} warning(s)")
    if not errors and not warnings:
        print("clean")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a permission model (menu tree, roles, grants, scopes, plans).",
    )
    parser.add_argument("model", help="path to permission-model.json")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--json", dest="as_json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    path = Path(args.model)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: no such file: {path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: {path} is not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(raw, dict):
        print(f"ERROR: {path} must contain a JSON object", file=sys.stderr)
        return 2

    findings, stats = validate(raw)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]

    if args.as_json:
        print(json.dumps({
            "ok": not errors and not (args.strict and warnings),
            "stats": stats,
            "errors": [{"code": f.code, "message": f.message, "hint": f.hint} for f in errors],
            "warnings": [{"code": f.code, "message": f.message, "hint": f.hint} for f in warnings],
        }, ensure_ascii=False, indent=2))
    else:
        render(path, findings, stats)

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
