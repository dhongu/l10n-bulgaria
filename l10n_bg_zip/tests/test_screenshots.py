# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
#
# Capturi de ecran pentru fișa consultant (readme/FISA_CONSULTANT.md, în RO, în
# static/description/) și pentru readme/USAGE.md (în EN, în static/description/en/).
#
# Localitățile sunt cele reale din data/res.city.csv (GeoNames); partenerii sunt de exemplu.
# Codul poștal se tastează în browser, ca operatorul.
#
# Rulare — RESTRÂNSĂ LA CLASĂ, altfel se rescriu capturile tuturor modulelor cu test de fișe:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_bg_zip,deltatech_doc_screenshots \
#       --test-tags=/l10n_bg_zip:TestBgZipScreenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    try:
        from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
    except ImportError:
        ScreenshotCase = None


def wait(ms):
    return f"await new Promise((resolve) => setTimeout(resolve, {ms}));"


# caută în lista de localități după codul poștal (5300: Gabrovo și satele din jur)
SEARCH_CAP = (
    """
async () => {
    const input = document.querySelector(".o_searchview_input");
    input.focus();
    input.value = "5300";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    """
    + wait(800)
    + """
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    """
    + wait(2000)
    + """
}
"""
)


def type_zip(zip_code, open_city=False):
    """Tastează codul poștal în adresa partenerului; opțional îl caută apoi în lista de localități."""
    script = """
async () => {
    const style = document.createElement("style");
    style.textContent = ".o_form_view [data-fise-badge] { left: -30px !important; }";
    document.head.appendChild(style);
    const input = document.querySelector("div[name='zip'] input");
    input.focus();
    input.value = "ZIP_CODE";
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    input.blur();
    """ + wait(2000)
    if open_city:
        script += (
            """
    const city = document.querySelector("div[name='city_id'] input");
    city.focus();
    city.value = "ZIP_CODE";
    city.dispatchEvent(new Event("input", { bubbles: true }));
    for (let i = 0; i < 50 && !document.querySelector(".o-autocomplete--dropdown-item"); i++) {
        """
            + wait(200)
            + """
    }
    """
        )
    return (script + "\n}\n").replace("ZIP_CODE", zip_code)


# selectează contactele italiene din listă și deschide meniul Acțiuni
OPEN_ACTIONS = (
    """
async () => {
    document.querySelector("thead .o_list_record_selector input").click();
    """
    + wait(800)
    + """
    document.querySelector(".o_cp_action_menus button").click();
    """
    + wait(1000)
    + """
}
"""
)

ADDRESS = ["div[name='zip']", "div[name='city_id']", "div[name='state_id']"]


@tagged("-at_install", "post_install", "fise_screenshots")
class TestBgZipScreenshots(ScreenshotCase or object):
    screenshots_module = "l10n_bg_zip"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="RO Company")
        env = cls.env
        bulgaria = env.ref("base.bg")
        Partner = env["res.partner"]
        cls.partner_haskovo = Partner.create(
            {
                "name": "Primer Haskovo OOD",
                "is_company": True,
                "country_id": bulgaria.id,
                "street": "ul. Rakovski 7",
                "vat": "BG123456786",
            }
        )
        cls.partner_gabrovo = Partner.create(
            {
                "name": "Primer Gabrovo OOD",
                "is_company": True,
                "country_id": bulgaria.id,
                "street": "ul. Opalchenska 12",
                "vat": "BG175074752",
            }
        )
        # contacte importate cu orașul scris liber, fără localitate din listă și fără provincie
        cls.imported = Partner.with_context(tracking_disable=True).create(
            [
                {"name": "Klient Plovdiv", "country_id": bulgaria.id, "city": "Plovdiv", "zip": "BG-4000"},
                {"name": "Klient Varna", "country_id": bulgaria.id, "city": "Varna", "zip": "9000"},
                {"name": "Klient Ruse", "country_id": bulgaria.id, "city": "Ruse", "zip": "7000"},
            ]
        )
        cls.city_action = env.ref("base_address_extended.action_res_city_tree")
        cls.contacts_action = env.ref("contacts.action_contacts")
        cls.menu = env.ref("contacts.menu_contacts")
        env.flush_all()

    def _form_url(self, partner):
        return f"id={partner.id}&model=res.partner&view_type=form&menu_id={self.menu.id}"

    def _shots(self):
        return [
            {
                "url": f"action={self.city_action.id}&view_type=list&menu_id={self.menu.id}",
                "name": "01_lista_localitati_cap.png",
                "wait": ".o_list_view .o_data_row",
                "eval": SEARCH_CAP,
                "eval_wait": 1000,
                "highlight": ".o_searchview",
            },
            {
                "url": self._form_url(self.partner_haskovo),
                "name": "02_partener_cap_unic.png",
                "wait": ".o_form_view div[name='zip'] input",
                "eval": type_zip("6300"),
                "eval_wait": 1000,
                "highlight": ADDRESS,
                "settle": 1500,
            },
            {
                "url": self._form_url(self.partner_gabrovo),
                "name": "03_partener_cap_comun.png",
                "wait": ".o_form_view div[name='zip'] input",
                "eval": type_zip("5300", open_city=True),
                "eval_wait": 1000,
                "highlight": ADDRESS,
                "settle": 1500,
            },
            {
                "url": f"action={self.contacts_action.id}&view_type=list&menu_id={self.menu.id}",
                "name": "04_actiune_contacte_existente.png",
                "wait": ".o_list_view .o_data_row",
                "eval": OPEN_ACTIONS,
                "eval_wait": 1000,
                "settle": 1000,
            },
        ]

    def _shot_after_action(self):
        plovdiv = self.imported.filtered(lambda p: p.name == "Klient Plovdiv")
        return {
            "url": self._form_url(plovdiv),
            "name": "05_contact_dupa_actiune.png",
            "wait": ".o_form_view div[name='zip'] input",
            "highlight": ADDRESS,
        }

    def _capture(self, lang):
        self.capture_screenshots(self._shots(), lang=lang)
        # rezultatul acțiunii „Bulgaria: completează localitatea din codul poștal”
        self.imported.l10n_bg_fix_city_from_zip()
        self.env.flush_all()
        self.capture_screenshots([self._shot_after_action()], lang=lang)

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")
