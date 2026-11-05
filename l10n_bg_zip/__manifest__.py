# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Bulgaria - City from ZIP",
    "summary": "Bulgarian provinces and localities with postal code, filled in from the ZIP",
    "version": "20.0.1.0.1",
    "author": "Terrabit",
    "website": "https://www.terrabit.ro",
    "category": "Localization",
    "countries": ["bg"],
    "license": "LGPL-3",
    "development_status": "Beta",
    "depends": ["base_address_extended"],
    "data": [
        "data/res_country_state_data.xml",
        "data/res.city.csv",
        "data/res_country_data.xml",
        "data/ir_actions_server.xml",
        "data/ir_cron.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "maintainers": ["dhongu"],
}
