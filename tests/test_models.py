"""Tests for Pydantic models."""

import unittest

from pydantic import ValidationError

from bexio.models import (
    KbInvoice,
    KbOrder,
    KbPositionCustom,
    KbPositionDiscount,
    OrderRepetition,
)


class TestKbOrder(unittest.TestCase):
    def _minimal(self, **overrides):
        body = {"contact_id": 269, "user_id": 1, "title": "Test"}
        body.update(overrides)
        return body

    def test_minimal_valid(self):
        order = KbOrder.model_validate(self._minimal())
        self.assertEqual(order.contact_id, 269)
        self.assertEqual(order.mwst_type, 0)
        self.assertTrue(order.mwst_is_net)

    def test_with_position(self):
        body = self._minimal(positions=[
            {"type": "KbPositionCustom",
             "text": "<strong>Grow</strong><br />Service",
             "unit_price": "349.00"},
        ])
        order = KbOrder.model_validate(body)
        self.assertEqual(len(order.positions), 1)
        self.assertIsInstance(order.positions[0], KbPositionCustom)

    def test_show_position_nr_rejected(self):
        body = self._minimal(show_position_nr=True)
        with self.assertRaises(ValidationError) as cm:
            KbOrder.model_validate(body)
        self.assertIn("show_position_nr", str(cm.exception))

    def test_markdown_in_header_rejected(self):
        body = self._minimal(header="Hallo **Andreas**")
        with self.assertRaises(ValidationError) as cm:
            KbOrder.model_validate(body)
        self.assertIn("HTML, not Markdown", str(cm.exception))

    def test_markdown_in_footer_rejected(self):
        body = self._minimal(footer="**Grüsse**")
        with self.assertRaises(ValidationError) as cm:
            KbOrder.model_validate(body)
        self.assertIn("HTML, not Markdown", str(cm.exception))

    def test_markdown_in_position_text_rejected(self):
        body = self._minimal(positions=[
            {"type": "KbPositionCustom",
             "text": "**Bold title**",
             "unit_price": "100"},
        ])
        with self.assertRaises(ValidationError) as cm:
            KbOrder.model_validate(body)
        self.assertIn("HTML, not Markdown", str(cm.exception))

    def test_missing_contact_id(self):
        with self.assertRaises(ValidationError):
            KbOrder.model_validate({"user_id": 1, "title": "X"})


class TestPositionDiscriminator(unittest.TestCase):
    def test_picks_custom(self):
        order = KbOrder.model_validate({
            "contact_id": 1, "user_id": 1, "title": "X",
            "positions": [{"type": "KbPositionCustom",
                           "text": "<strong>x</strong>", "unit_price": "1"}],
        })
        self.assertIsInstance(order.positions[0], KbPositionCustom)

    def test_picks_discount(self):
        order = KbOrder.model_validate({
            "contact_id": 1, "user_id": 1, "title": "X",
            "positions": [{"type": "KbPositionDiscount",
                           "text": "50%", "value": "50", "is_percentual": True}],
        })
        self.assertIsInstance(order.positions[0], KbPositionDiscount)

    def test_unknown_type_rejected(self):
        with self.assertRaises(ValidationError):
            KbOrder.model_validate({
                "contact_id": 1, "user_id": 1, "title": "X",
                "positions": [{"type": "KbPositionWhatever", "text": "x"}],
            })


class TestOrderRepetition(unittest.TestCase):
    def test_monthly_fixed_day(self):
        spec = OrderRepetition.model_validate({
            "start": "2026-06-01", "end": None,
            "repetition": {"type": "monthly", "interval": 1, "schedule": "fixed_day"},
        })
        dumped = spec.model_dump(mode="json")
        self.assertEqual(dumped["repetition"]["schedule"], "fixed_day")

    def test_monthly_requires_schedule(self):
        with self.assertRaises(ValidationError):
            OrderRepetition.model_validate({
                "start": "2026-06-01",
                "repetition": {"type": "monthly", "interval": 1},
            })

    def test_weekly_requires_weekdays(self):
        with self.assertRaises(ValidationError):
            OrderRepetition.model_validate({
                "start": "2026-06-01",
                "repetition": {"type": "weekly", "interval": 1},
            })

    def test_weekly_with_weekdays(self):
        spec = OrderRepetition.model_validate({
            "start": "2026-06-01",
            "repetition": {"type": "weekly", "interval": 1,
                           "weekdays": ["monday", "wednesday"]},
        })
        dumped = spec.model_dump(mode="json")
        self.assertEqual(dumped["repetition"]["weekdays"], ["monday", "wednesday"])

    def test_yearly_no_schedule(self):
        spec = OrderRepetition.model_validate({
            "start": "2026-06-01",
            "repetition": {"type": "yearly", "interval": 1},
        })
        self.assertEqual(spec.repetition.type, "yearly")

    def test_schedule_on_non_monthly_rejected(self):
        with self.assertRaises(ValidationError):
            OrderRepetition.model_validate({
                "start": "2026-06-01",
                "repetition": {"type": "yearly", "interval": 1, "schedule": "fixed_day"},
            })

    def test_unknown_type_rejected(self):
        with self.assertRaises(ValidationError):
            OrderRepetition.model_validate({
                "start": "2026-06-01",
                "repetition": {"type": "fortnightly", "interval": 1},
            })

    def test_end_before_start_rejected(self):
        with self.assertRaises(ValidationError):
            OrderRepetition.model_validate({
                "start": "2026-06-01", "end": "2026-05-01",
                "repetition": {"type": "monthly", "interval": 1, "schedule": "fixed_day"},
            })


class TestKbInvoice(unittest.TestCase):
    def test_minimal_valid(self):
        invoice = KbInvoice.model_validate({
            "contact_id": 269, "user_id": 1, "title": "Test",
            "is_valid_from": "2026-05-04",
        })
        self.assertEqual(invoice.is_valid_from, "2026-05-04")

    def test_show_position_nr_allowed(self):
        # Unlike kb_order, kb_invoice DOES accept show_position_nr.
        invoice = KbInvoice.model_validate({
            "contact_id": 1, "user_id": 1, "title": "X",
            "is_valid_from": "2026-05-04",
            "show_position_nr": True,
        })
        self.assertTrue(invoice.show_position_nr)

    def test_missing_is_valid_from(self):
        with self.assertRaises(ValidationError):
            KbInvoice.model_validate({
                "contact_id": 1, "user_id": 1, "title": "X",
            })


if __name__ == "__main__":
    unittest.main()
