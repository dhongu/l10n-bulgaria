# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo.tests import Form, TransactionCase, tagged

from odoo.addons.l10n_bg_zip.hooks import _normalize


@tagged("post_install", "-at_install")
class TestCityFromZip(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bulgaria = cls.env.ref("base.bg")
        cls.Partner = cls.env["res.partner"]
        cls.plovdiv_state = cls.env.ref("l10n_bg_zip.state_bg_16")

    def _bg_city(self, zip_code, name):
        return self.env["res.city"].search(
            [("country_id", "=", self.bulgaria.id), ("zipcode", "=", zip_code), ("name", "=", name)]
        )

    def test_data_loaded(self):
        self.assertTrue(self.bulgaria.enforce_cities)
        states = self.env["res.country.state"].search([("country_id", "=", self.bulgaria.id)])
        self.assertEqual(len(states), 28)
        sofia = self._bg_city("1000", "Sofia")
        self.assertEqual(len(sofia), 1)
        self.assertEqual(sofia.state_id, self.env.ref("l10n_bg_zip.state_bg_22"))

    def test_unique_zip(self):
        city, state = self.Partner._l10n_bg_city_from_zip("6300")
        self.assertEqual(city, self._bg_city("6300", "Haskovo"))
        self.assertEqual(state, self.env.ref("l10n_bg_zip.state_bg_26"))
        # spaces and the "BG-" prefix are dropped
        city, state = self.Partner._l10n_bg_city_from_zip("BG-9000")
        self.assertEqual(city, self._bg_city("9000", "Varna"))

    def test_shared_zip_gives_province(self):
        # 4000 is Plovdiv and Voysil: only the province is known
        city, state = self.Partner._l10n_bg_city_from_zip("4000")
        self.assertFalse(city)
        self.assertEqual(state, self.plovdiv_state)
        city, state = self.Partner._l10n_bg_city_from_zip("4000", "plovdiv")
        self.assertEqual(city, self._bg_city("4000", "Plovdiv"))

    def test_shared_zip_cyrillic_name(self):
        self.env["res.lang"]._activate_lang("bg_BG")
        self.env["ir.module.module"]._load_module_terms(["l10n_bg_zip"], ["bg_BG"])
        plovdiv = self._bg_city("4000", "Plovdiv")
        self.assertEqual(plovdiv.with_context(lang="bg_BG").name, "Пловдив")
        city, state = self.Partner._l10n_bg_city_from_zip("4000", "Пловдив")
        self.assertEqual(city, plovdiv)

    def test_zip_in_two_provinces(self):
        # 2624 is shared by localities of Kyustendil and Sofia: no province is guessed
        city, state = self.Partner._l10n_bg_city_from_zip("2624")
        self.assertFalse(city)
        self.assertFalse(state)

    def test_onchange_zip(self):
        partner_form = Form(self.Partner)
        partner_form.name = "Primer OOD"
        partner_form.country_id = self.bulgaria
        partner_form.zip = "6300"
        self.assertEqual(partner_form.city_id, self._bg_city("6300", "Haskovo"))
        self.assertEqual(partner_form.city, "Haskovo")
        self.assertEqual(partner_form.state_id, self.env.ref("l10n_bg_zip.state_bg_26"))

    def test_fix_city_from_zip(self):
        partner = self.Partner.create(
            {"name": "Primer OOD", "country_id": self.bulgaria.id, "city": "Plovdiv", "zip": "4000"}
        )
        other = self.Partner.create(
            {"name": "Ion Popescu", "country_id": self.env.ref("base.ro").id, "city": "Plovdiv", "zip": "4000"}
        )
        (partner | other).l10n_bg_fix_city_from_zip()
        self.assertEqual(partner.city_id, self._bg_city("4000", "Plovdiv"))
        self.assertEqual(partner.state_id, self.plovdiv_state)
        self.assertFalse(other.city_id)

    def test_relink_batch(self):
        partner = self.Partner.create(
            {"name": "Primer OOD", "country_id": self.bulgaria.id, "city": "Haskovo", "zip": "6300"}
        )
        last_id, count = self.Partner._l10n_bg_relink_batch(partner.id - 1)
        self.assertGreaterEqual(count, 1)
        self.assertEqual(partner.city_id, self._bg_city("6300", "Haskovo"))

    def test_province_name_matching(self):
        self.assertEqual(_normalize("Sofia Province"), _normalize("Sofia"))
        self.assertEqual(_normalize("Sofia City Province"), _normalize("Sofia City"))
        self.assertEqual(_normalize("Област Варна"), _normalize("Варна"))
        self.assertEqual(_normalize("Veliko Tărnovo"), _normalize("Veliko Tarnovo"))
