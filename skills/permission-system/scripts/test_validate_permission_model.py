#!/usr/bin/env python3
"""Tests for validate_permission_model.py.

Run:  python -m unittest discover -s skills/permission-system/scripts
  or: python skills/permission-system/scripts/test_validate_permission_model.py
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_permission_model import matches, validate  # noqa: E402

EXAMPLE = (
    Path(__file__).resolve().parents[1]
    / "assets" / "templates" / "permission-model.example.json"
)


def codes(findings, level=None):
    return sorted(f.code for f in findings if level is None or f.level == level)


def minimal(**overrides):
    """A tiny valid model: one dir, one menu, one read button, one role."""
    model = {
        "permissions": [
            {"code": "shop", "name": "Shop", "type": "dir", "parent": None},
            {"code": "shop:order", "name": "Orders", "type": "menu",
             "parent": "shop", "route_path": "/shop/order"},
            {"code": "shop:order:list", "name": "View", "type": "button",
             "parent": "shop:order", "action": "read"},
        ],
        "roles": [
            {"code": "admin", "name": "Admin", "builtin": True,
             "permissions": ["shop:*"], "data_scope": "ALL"},
        ],
    }
    model.update(overrides)
    return model


class TestWildcards(unittest.TestCase):
    def test_star_matches_everything(self):
        self.assertTrue(matches("*", "anything:at:all"))

    def test_prefix_matches_self_and_descendants(self):
        self.assertTrue(matches("shop:*", "shop"))
        self.assertTrue(matches("shop:*", "shop:order"))
        self.assertTrue(matches("shop:*", "shop:order:list"))

    def test_prefix_does_not_match_siblings(self):
        self.assertFalse(matches("shop:*", "shopping"))
        self.assertFalse(matches("shop:*", "warehouse:order"))

    def test_exact_match(self):
        self.assertTrue(matches("shop:order", "shop:order"))
        self.assertFalse(matches("shop:order", "shop:order:list"))


class TestBundledExample(unittest.TestCase):
    """The shipped template is what people copy, so it must be spotless."""

    def test_example_file_exists(self):
        self.assertTrue(EXAMPLE.is_file(), f"missing template: {EXAMPLE}")

    def test_example_validates_clean(self):
        raw = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        findings, stats = validate(raw)
        self.assertEqual(
            [], [f"{f.level} {f.code}: {f.message}" for f in findings],
            "the bundled example must validate with zero findings",
        )
        self.assertGreater(stats["permissions"], 10)
        self.assertGreater(stats["roles"], 3)


class TestMinimalModelIsClean(unittest.TestCase):
    def test_no_findings(self):
        findings, _ = validate(minimal(plans=[{"code": "all", "permissions": ["*"]}]))
        self.assertEqual([], [f"{f.code}: {f.message}" for f in findings])


class TestPermissionTreeErrors(unittest.TestCase):
    def test_duplicate_code(self):
        m = minimal()
        m["permissions"].append(
            {"code": "shop:order:list", "name": "Dup", "type": "button",
             "parent": "shop:order", "action": "read"})
        self.assertIn("E001", codes(validate(m)[0], "error"))

    def test_malformed_code(self):
        m = minimal()
        m["permissions"][2]["code"] = "Shop:Order:List"
        self.assertIn("E002", codes(validate(m)[0], "error"))

    def test_unknown_parent(self):
        m = minimal()
        m["permissions"][2]["parent"] = "shop:ordre"
        found = [f for f in validate(m)[0] if f.code == "E003"]
        self.assertTrue(found)
        self.assertIn("shop:order", found[0].hint, "should suggest the near match")

    def test_parent_cycle(self):
        m = {
            "permissions": [
                {"code": "a:b", "name": "B", "type": "dir", "parent": "a:b:c"},
                {"code": "a:b:c", "name": "C", "type": "dir", "parent": "a:b"},
            ],
            "roles": [],
        }
        self.assertIn("E004", codes(validate(m)[0], "error"))

    def test_invalid_type(self):
        m = minimal()
        m["permissions"][1]["type"] = "page"
        self.assertIn("E005", codes(validate(m)[0], "error"))

    def test_button_under_dir(self):
        m = minimal()
        m["permissions"].append(
            {"code": "shop:direct", "name": "Nope", "type": "button",
             "parent": "shop", "action": "read"})
        self.assertIn("E006", codes(validate(m)[0], "error"))

    def test_menu_under_menu(self):
        m = minimal()
        m["permissions"].append(
            {"code": "shop:order:sub", "name": "Sub", "type": "menu",
             "parent": "shop:order", "route_path": "/x"})
        self.assertIn("E007", codes(validate(m)[0], "error"))

    def test_menu_without_route(self):
        m = minimal()
        del m["permissions"][1]["route_path"]
        self.assertIn("E008", codes(validate(m)[0], "error"))

    def test_button_with_route(self):
        m = minimal()
        m["permissions"][2]["route_path"] = "/shop/order/list"
        self.assertIn("E009", codes(validate(m)[0], "error"))

    def test_external_link_needs_scheme(self):
        m = minimal()
        m["permissions"][0]["is_external"] = True
        m["permissions"][0]["route_path"] = "docs.example.com"
        self.assertIn("E010", codes(validate(m)[0], "error"))

    def test_child_code_must_extend_parent(self):
        m = minimal()
        m["permissions"][2]["code"] = "other:order:list"
        self.assertIn("E015", codes(validate(m)[0], "error"))


class TestRoleErrors(unittest.TestCase):
    def test_grant_matching_nothing(self):
        m = minimal()
        m["roles"][0]["permissions"] = ["shop:order:creat"]
        found = [f for f in validate(m)[0] if f.code == "E011"]
        self.assertTrue(found)

    def test_typo_suggestion(self):
        m = minimal()
        m["permissions"].append(
            {"code": "shop:order:create", "name": "Create", "type": "button",
             "parent": "shop:order", "action": "write"})
        m["roles"][0]["permissions"] = ["shop:order:list", "shop:order:creat", "shop:order"]
        found = [f for f in validate(m)[0] if f.code == "E011"]
        self.assertTrue(found)
        self.assertIn("shop:order:create", found[0].hint)

    def test_duplicate_role_code(self):
        m = minimal()
        m["roles"].append({"code": "admin", "name": "Admin 2", "permissions": ["shop:*"]})
        self.assertIn("E016", codes(validate(m)[0], "error"))

    def test_invalid_data_scope(self):
        m = minimal()
        m["roles"][0]["data_scope"] = "EVERYTHING"
        self.assertIn("E013", codes(validate(m)[0], "error"))

    def test_custom_scope_without_departments(self):
        m = minimal()
        m["roles"][0]["data_scope"] = "CUSTOM"
        self.assertIn("E014", codes(validate(m)[0], "error"))

    def test_custom_scope_with_departments_is_fine(self):
        m = minimal()
        m["roles"][0]["data_scope"] = "CUSTOM"
        m["roles"][0]["depts"] = ["d1"]
        self.assertNotIn("E014", codes(validate(m)[0], "error"))

    def test_mutex_unknown_role(self):
        m = minimal(mutex=[["admin", "ghost"]])
        self.assertIn("E012", codes(validate(m)[0], "error"))

    def test_mutex_needs_two_roles(self):
        m = minimal(mutex=[["admin"]])
        self.assertIn("E012", codes(validate(m)[0], "error"))


class TestTheWarningsThatEarnTheirKeep(unittest.TestCase):
    """These are the checks a human reviewer misses in a large matrix."""

    def _with_crud(self, role_perms):
        m = minimal()
        m["permissions"].append(
            {"code": "shop:order:edit", "name": "Edit", "type": "button",
             "parent": "shop:order", "action": "write"})
        m["roles"] = [
            {"code": "admin", "name": "Admin", "builtin": True,
             "permissions": ["shop:*"], "data_scope": "ALL"},
            {"code": "clerk", "name": "Clerk", "builtin": True,
             "permissions": role_perms, "data_scope": "SELF"},
        ]
        return m

    def test_write_without_read(self):
        m = self._with_crud(["shop:order", "shop:order:edit"])
        found = [f for f in validate(m)[0] if f.code == "W003"]
        self.assertTrue(found)
        self.assertIn("clerk", found[0].message)

    def test_write_with_read_is_fine(self):
        m = self._with_crud(["shop:order", "shop:order:list", "shop:order:edit"])
        self.assertNotIn("W003", codes(validate(m)[0], "warning"))

    def test_button_without_parent_menu(self):
        m = self._with_crud(["shop:order:list", "shop:order:edit"])
        found = [f for f in validate(m)[0] if f.code == "W004"]
        self.assertTrue(found)
        self.assertIn("shop:order", found[0].message)

    def test_permission_granted_to_nobody(self):
        m = minimal()
        m["permissions"].append(
            {"code": "shop:order:export", "name": "Export", "type": "button",
             "parent": "shop:order", "action": "read"})
        m["roles"][0]["permissions"] = ["shop:order", "shop:order:list"]
        found = [f for f in validate(m)[0] if f.code == "W001"]
        self.assertTrue(any("shop:order:export" in f.message for f in found))

    def test_role_with_no_permissions(self):
        m = minimal()
        m["roles"].append({"code": "empty", "name": "Empty", "permissions": []})
        self.assertIn("W002", codes(validate(m)[0], "warning"))

    def test_permission_in_no_plan(self):
        m = minimal(plans=[{"code": "basic", "permissions": ["shop", "shop:order"]}])
        found = [f for f in validate(m)[0] if f.code == "W005"]
        self.assertTrue(any("shop:order:list" in f.message for f in found))

    def test_plan_covering_everything_is_fine(self):
        m = minimal(plans=[{"code": "pro", "permissions": ["*"]}])
        self.assertNotIn("W005", codes(validate(m)[0], "warning"))

    def test_plan_grant_matching_nothing(self):
        m = minimal(plans=[{"code": "pro", "permissions": ["warehouse:*"]}])
        self.assertIn("E017", codes(validate(m)[0], "error"))

    def test_wildcard_on_custom_role(self):
        m = minimal()
        m["roles"].append({"code": "custom", "name": "Custom", "builtin": False,
                           "permissions": ["shop:*"], "data_scope": "SELF"})
        self.assertIn("W008", codes(validate(m)[0], "warning"))

    def test_wildcard_on_builtin_role_is_fine(self):
        self.assertNotIn("W008", codes(validate(minimal())[0], "warning"))

    def test_menu_with_no_buttons(self):
        m = minimal()
        m["permissions"].append(
            {"code": "shop:report", "name": "Reports", "type": "menu",
             "parent": "shop", "route_path": "/shop/report"})
        found = [f for f in validate(m)[0] if f.code == "W006"]
        self.assertTrue(any("shop:report" in f.message for f in found))

    def test_no_builtin_roles_at_all(self):
        m = minimal()
        m["roles"][0]["builtin"] = False
        self.assertIn("W007", codes(validate(m)[0], "warning"))


class TestActionInference(unittest.TestCase):
    def test_infers_write_from_last_segment(self):
        """No explicit 'action' field -- the vocabulary should carry it."""
        m = minimal()
        m["permissions"].append(
            {"code": "shop:order:delete", "name": "Delete", "type": "button",
             "parent": "shop:order"})
        m["roles"] = [
            {"code": "admin", "name": "A", "builtin": True, "permissions": ["shop:*"]},
            {"code": "clerk", "name": "C", "builtin": True,
             "permissions": ["shop:order", "shop:order:delete"]},
        ]
        self.assertIn("W003", codes(validate(m)[0], "warning"))

    def test_unknown_action_is_not_flagged(self):
        m = minimal()
        m["permissions"].append(
            {"code": "shop:order:frobnicate", "name": "?", "type": "button",
             "parent": "shop:order"})
        m["roles"] = [
            {"code": "admin", "name": "A", "builtin": True, "permissions": ["shop:*"]},
            {"code": "clerk", "name": "C", "builtin": True,
             "permissions": ["shop:order", "shop:order:frobnicate"]},
        ]
        self.assertNotIn("W003", codes(validate(m)[0], "warning"))


class TestFieldRules(unittest.TestCase):
    def test_unknown_role(self):
        m = minimal(field_rules=[
            {"role": "ghost", "resource": "shop:order", "field": "total", "access": "read"}])
        self.assertIn("E018", codes(validate(m)[0], "error"))

    def test_invalid_access(self):
        m = minimal(field_rules=[
            {"role": "admin", "resource": "shop:order", "field": "total", "access": "peek"}])
        self.assertIn("E019", codes(validate(m)[0], "error"))

    def test_unknown_resource_is_a_warning(self):
        m = minimal(field_rules=[
            {"role": "admin", "resource": "nope:nope", "field": "total", "access": "read"}])
        self.assertIn("W011", codes(validate(m)[0], "warning"))


class TestEmptyInput(unittest.TestCase):
    def test_no_permissions(self):
        findings, stats = validate({"permissions": [], "roles": []})
        self.assertIn("E000", codes(findings, "error"))
        self.assertEqual(0, stats["permissions"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
