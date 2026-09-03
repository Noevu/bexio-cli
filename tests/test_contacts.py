"""Tests for contact commands."""

import io
import json
import unittest
from unittest.mock import patch

from tests.helpers import capture_with_responses

# Feldnamen wie in der echten Antwort von `GET /2.0/contact/{id}`, am 2026-09-02
# gegen die Live-API gemessen. Die frühere Fassung führte `name`, `firstname` und
# `lastname` — Felder, die Bexio NIE zurückgibt. Dadurch waren diese Tests grün,
# während `contacts list`, `show` und `search` in der Praxis eine leere Namensspalte
# zeigten und die Suche mit HTTP 400 abbrach.
CONTACT = {
    "id": 246,
    "contact_type_id": 1,
    "name_1": "Ausgleichskasse der AIHK",
    "name_2": "",
    "mail": "info@aihk.ch",
    "phone_fixed": "+41 62 837 97 00",
}

# Person: `name_1` ist der NACHname, `name_2` der Vorname.
PERSON = {
    "id": 245,
    "contact_type_id": 2,
    "name_1": "Imperia",
    "name_2": "Anna",
    "mail": "anna@aihk.ch",
    "phone_fixed": "",
}


class TestContactsList(unittest.TestCase):
    def test_shows_org_name(self):
        out = capture_with_responses(["contacts", "list"], [[CONTACT]])
        self.assertIn("Ausgleichskasse der AIHK", out)
        self.assertIn("info@aihk.ch", out)

    def test_shows_person_name_from_parts(self):
        out = capture_with_responses(["contacts", "list"], [[PERSON]])
        self.assertIn("Anna Imperia", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "contacts", "list"], [[CONTACT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 246)


class TestContactsShow(unittest.TestCase):
    def test_shows_all_fields(self):
        out = capture_with_responses(["contacts", "show", "246"], [CONTACT])
        self.assertIn("246", out)
        self.assertIn("Ausgleichskasse der AIHK", out)
        self.assertIn("info@aihk.ch", out)
        self.assertIn("office.bexio.com", out)

    def test_person_name_from_parts(self):
        out = capture_with_responses(["contacts", "show", "245"], [PERSON])
        self.assertIn("Anna Imperia", out)


class TestContactsSearch(unittest.TestCase):
    def test_posts_search_body(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, body))
            return [CONTACT]

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "contacts", "search", "AIHK"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        method, path, body = captured[0]
        self.assertEqual(method, "POST")
        self.assertIn("contact/search", path)
        self.assertEqual(body[0]["value"], "AIHK")
        # `name` ist KEIN gültiges Suchfeld — Bexio antwortet HTTP 400
        # ("The following search parameters could not have been applied").
        self.assertEqual(body[0]["field"], "name_1")

    def test_searches_both_name_fields(self):
        """Ein Vorname steht in `name_2` — eine Suche nur über `name_1` fände ihn nie."""
        captured = []

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, body))
            return []

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "contacts", "search", "Anna"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        felder = [body[0]["field"] for _m, _p, body in captured]
        self.assertEqual(felder, ["name_1", "name_2"])

    def test_empty_results_message(self):
        out = capture_with_responses(["contacts", "search", "nobody"], [[]])
        self.assertIn("No contacts", out)

    def test_json_output(self):
        out = capture_with_responses(["--json", "contacts", "search", "AIHK"], [[CONTACT]])
        parsed = json.loads(out)
        self.assertEqual(parsed[0]["id"], 246)


class TestContactsCreate(unittest.TestCase):
    def _capture_create(self, extra_args, response=None):
        captured = []
        resp = response or {"id": 300, "name": "New Corp"}

        def fake_request(self, method, path, params=None, body=None):
            captured.append((method, path, body))
            return resp

        buf = io.StringIO()
        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "contacts", "create"] + extra_args), \
             patch("sys.stdout", buf):
            from bexio.cli import main
            main()
        return buf.getvalue(), captured

    def test_posts_to_contact_endpoint(self):
        _, captured = self._capture_create(["--name", "AIHK"])
        self.assertEqual(captured[0][0], "POST")
        self.assertIn("/contact", captured[0][1])

    def test_company_name_uses_api_field_name_1(self):
        # Bexio rejects `name` with 422 "Unexpected extra form field named name"
        _, captured = self._capture_create(["--name", "AIHK"])
        body = captured[0][2]
        self.assertEqual(body["name_1"], "AIHK")
        self.assertNotIn("name", body)

    def test_person_fields_map_to_name_1_and_name_2(self):
        _, captured = self._capture_create(["--firstname", "Anna", "--lastname", "Imperia", "--email", "anna@test.ch"])
        body = captured[0][2]
        self.assertEqual(body["name_1"], "Imperia")   # surname
        self.assertEqual(body["name_2"], "Anna")      # given name
        self.assertEqual(body["mail"], "anna@test.ch")
        self.assertNotIn("firstname", body)
        self.assertNotIn("lastname", body)

    def test_mandatory_owner_fields_are_sent(self):
        # Bexio 422: "user_id: Pflichtfeld", "owner_id: Pflichtfeld"
        _, captured = self._capture_create(["--name", "AIHK"])
        body = captured[0][2]
        self.assertEqual(body["user_id"], 1)
        self.assertEqual(body["owner_id"], 1)

    def test_address_fields_map_to_bexio_names(self):
        # Bexio's writable address fields are street_name + house_number (+ addition),
        # postcode, city, country_id. The single 'address' field is read-only. NOE-3277.
        _, captured = self._capture_create([
            "--name", "AIHK",
            "--street", "Bahnhofstrasse", "--house-number", "1",
            "--address-addition", "c/o Meier",
            "--postcode", "5000", "--city", "Aarau", "--country-id", "1",
        ])
        body = captured[0][2]
        self.assertEqual(body["street_name"], "Bahnhofstrasse")
        self.assertEqual(body["house_number"], "1")
        self.assertEqual(body["address_addition"], "c/o Meier")
        self.assertEqual(body["postcode"], "5000")
        self.assertEqual(body["city"], "Aarau")
        self.assertEqual(body["country_id"], 1)
        self.assertNotIn("address", body)

    def test_prints_id_and_url(self):
        out, _ = self._capture_create(["--name", "AIHK"])
        self.assertIn("300", out)
        self.assertIn("office.bexio.com", out)

    def test_no_name_exits(self):
        with self.assertRaises(SystemExit):
            with patch("bexio.auth.get_token", return_value="FAKE"), \
                 patch("sys.argv", ["bexio", "contacts", "create"]):
                from bexio.cli import main
                main()

    def test_json_output(self):
        out = capture_with_responses(["--json", "contacts", "create", "--name", "AIHK"],
                                     [{"id": 300, "name": "New Corp"}])
        parsed = json.loads(out)
        self.assertEqual(parsed["id"], 300)


# A Bexio contact edit is POST /2.0/contact/{id} (v2EditContact) and REPLACES the
# whole record — so the CLI reads the existing contact, overlays the changed fields,
# and posts the full body back. Otherwise omitted fields (address, phone…) get wiped.
EXISTING_CONTACT = {
    "id": 246, "contact_type_id": 1, "name_1": "AIHK", "name_2": None,
    "user_id": 1, "owner_id": 1, "nr": "1234",
    "mail": "info@aihk.ch", "phone_fixed": "+41 62 837 97 00",
    "street_name": None, "house_number": None, "postcode": None, "city": None,
    "country_id": None, "contact_group_ids": [5, 6],
}


class TestContactsEdit(unittest.TestCase):
    def _capture_edit(self, argv_tail):
        calls = []

        def fake_request(self, method, path, params=None, body=None, base=None, raw=False):
            calls.append((method, path, body))
            if method == "GET":
                return dict(EXISTING_CONTACT)
            return {"id": 246}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "contacts", "edit", "246"] + argv_tail), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()
        return calls

    def test_fetches_then_posts_to_contact_id(self):
        calls = self._capture_edit(["--email", "new@test.ch"])
        self.assertEqual(calls[0][0], "GET")
        self.assertIn("/contact/246", calls[0][1])
        self.assertEqual(calls[1][0], "POST")  # edit = POST, not PUT
        self.assertEqual(calls[1][1], "/contact/246")

    def test_change_is_overlaid(self):
        calls = self._capture_edit(["--email", "new@test.ch"])
        self.assertEqual(calls[1][2]["mail"], "new@test.ch")

    def test_second_email_is_settable(self):
        # A person can carry two addresses; `mail_second` was already preserved on
        # echo-back but had no flag, so the only way to set it was the raw API.
        calls = self._capture_edit(["--email-second", "beni.zweit@test.ch"])
        self.assertEqual(calls[1][2]["mail_second"], "beni.zweit@test.ch")

    def test_second_email_leaves_the_primary_alone(self):
        calls = self._capture_edit(["--email-second", "beni.zweit@test.ch"])
        self.assertEqual(calls[1][2]["mail"], "info@aihk.ch")


class TestContactsEditSalutationZero(unittest.TestCase):
    """Bexio returns `salutation_id: 0` for a contact without a salutation but
    refuses to accept it on write ("Diese Eingabe ist nicht korrekt", 422). Echoing
    the GET back therefore breaks the edit for 243 of 251 live contacts — measured
    2026-09-02, found only by running the command against the real API."""

    def _capture_edit(self, argv_tail):
        calls = []
        contact = dict(EXISTING_CONTACT, salutation_id=0)

        def fake_request(self, method, path, params=None, body=None, base=None, raw=False):
            calls.append((method, path, body))
            return dict(contact) if method == "GET" else {"id": 246}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "contacts", "edit", "246"] + argv_tail), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()
        return calls

    def test_zero_salutation_is_not_echoed_back(self):
        calls = self._capture_edit(["--email", "neu@test.ch"])
        self.assertNotIn("salutation_id", calls[1][2])

    def test_the_rest_of_the_record_still_travels(self):
        body = self._capture_edit(["--email", "neu@test.ch"])[1][2]
        self.assertEqual(body["name_1"], "AIHK")
        self.assertEqual(body["mail"], "neu@test.ch")

    def test_existing_fields_preserved_full_replace(self):
        # Only the email changes; nothing else may be wiped by the replacement post.
        calls = self._capture_edit(["--email", "new@test.ch"])
        body = calls[1][2]
        self.assertEqual(body["name_1"], "AIHK")
        self.assertEqual(body["contact_type_id"], 1)
        self.assertEqual(body["user_id"], 1)
        self.assertEqual(body["owner_id"], 1)
        self.assertEqual(body["phone_fixed"], "+41 62 837 97 00")
        self.assertEqual(body["nr"], "1234")
        self.assertEqual(body["contact_group_ids"], "5,6")  # list → csv on echo-back

    def test_adds_address(self):
        calls = self._capture_edit([
            "--street", "Bahnhofstrasse", "--house-number", "1",
            "--postcode", "5000", "--city", "Aarau", "--country-id", "1",
        ])
        body = calls[1][2]
        self.assertEqual(body["street_name"], "Bahnhofstrasse")
        self.assertEqual(body["house_number"], "1")
        self.assertEqual(body["postcode"], "5000")
        self.assertEqual(body["city"], "Aarau")
        self.assertEqual(body["country_id"], 1)
        self.assertEqual(body["name_1"], "AIHK")  # untouched

    def test_name_maps_to_name_1(self):
        calls = self._capture_edit(["--name", "New Name"])
        body = calls[1][2]
        self.assertEqual(body["name_1"], "New Name")
        self.assertNotIn("name", body)

    def test_person_name_parts_map(self):
        calls = self._capture_edit(["--firstname", "Anna", "--lastname", "Imperia"])
        body = calls[1][2]
        self.assertEqual(body["name_1"], "Imperia")
        self.assertEqual(body["name_2"], "Anna")

    def test_prints_confirmation(self):
        out = capture_with_responses(
            ["contacts", "edit", "246", "--name", "New Name"],
            [dict(EXISTING_CONTACT), {"id": 246}],
        )
        self.assertIn("updated", out)
        self.assertIn("246", out)


class TestContactsDelete(unittest.TestCase):
    def test_prints_confirmation(self):
        out = capture_with_responses(["contacts", "delete", "246"], [{"success": True}])
        self.assertIn("deleted", out)
        self.assertIn("246", out)

    def test_deletes_correct_endpoint(self):
        captured = []

        def fake_request(self, method, path, params=None, body=None, base=None, accept="application/json"):
            captured.append((method, path))
            return {"success": True}

        with patch("bexio.client.BexioClient._request", fake_request), \
             patch("bexio.auth.get_token", return_value="FAKE"), \
             patch("sys.argv", ["bexio", "contacts", "delete", "246"]), \
             patch("sys.stdout", io.StringIO()):
            from bexio.cli import main
            main()

        self.assertIn(("DELETE", "/contact/246"), captured)
