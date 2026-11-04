#!/usr/bin/env python3
# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
"""Generate the data of l10n_bg_zip from the GeoNames postal codes of Bulgaria.

Usage: python3 scripts/generate_city_data.py <path to BG.txt>

BG.txt comes from https://download.geonames.org/export/zip/BG.zip (GeoNames,
Creative Commons Attribution 4.0). Columns: country, postal code, place name
("Cyrillic / Latin"), province name, province code, ...

Writes:
- l10n_bg_zip/data/res.city.csv: the localities, named in Latin with the official
  Bulgarian transliteration (Transliteration Act, 2009), with the Cyrillic name in the
  column name@bg_BG (loaded by Odoo as the Bulgarian translation);
- l10n_bg_zip/i18n/bg.po and l10n_bg_zip.pot: the interface strings (UI_TRANSLATIONS);
- l10n_bg_zip/data/res_country_state_data.xml: the 28 provinces (in Latin: the name of a
  province is not translatable in Odoo).
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "l10n_bg_zip"

# GeoNames province code -> ISO 3166-2:BG code (xml id state_bg_<code>)
PROVINCES = {
    "BLG": "01", "BGS": "02", "VAR": "03", "VTR": "04", "VID": "05", "VRC": "06", "GAB": "07",
    "DOB": "08", "KRZ": "09", "KNL": "10", "LOV": "11", "MON": "12", "PAZ": "13", "PER": "14",
    "PVN": "15", "PDV": "16", "RAZ": "17", "RSE": "18", "SLS": "19", "SLV": "20", "SML": "21",
    "SOF": "22", "SFO": "23", "SZR": "24", "TGV": "25", "HKV": "26", "SHU": "27", "JAM": "28",
}  # fmt: skip

# ISO 3166-2:BG code, name in Latin, name in Cyrillic
STATES = [
    ("01", "Blagoevgrad", "Благоевград"), ("02", "Burgas", "Бургас"), ("03", "Varna", "Варна"),
    ("04", "Veliko Tarnovo", "Велико Търново"), ("05", "Vidin", "Видин"), ("06", "Vratsa", "Враца"),
    ("07", "Gabrovo", "Габрово"), ("08", "Dobrich", "Добрич"), ("09", "Kardzhali", "Кърджали"),
    ("10", "Kyustendil", "Кюстендил"), ("11", "Lovech", "Ловеч"), ("12", "Montana", "Монтана"),
    ("13", "Pazardzhik", "Пазарджик"), ("14", "Pernik", "Перник"), ("15", "Pleven", "Плевен"),
    ("16", "Plovdiv", "Пловдив"), ("17", "Razgrad", "Разград"), ("18", "Ruse", "Русе"),
    ("19", "Silistra", "Силистра"), ("20", "Sliven", "Сливен"), ("21", "Smolyan", "Смолян"),
    ("22", "Sofia City", "София (столица)"), ("23", "Sofia", "София"),
    ("24", "Stara Zagora", "Стара Загора"), ("25", "Targovishte", "Търговище"),
    ("26", "Haskovo", "Хасково"), ("27", "Shumen", "Шумен"), ("28", "Yambol", "Ямбол"),
]  # fmt: skip

# interface strings of the module (from i18n/l10n_bg_zip.pot), in Bulgarian
UI_TRANSLATIONS = [
    ("model:ir.model,name:l10n_bg_zip.model_res_partner", "Contact", "Контакт"),
    ("model:ir.model.fields,field_description:l10n_bg_zip.field_res_partner__display_name", "Display Name",
     "Показвано име"),
    ("model:ir.model.fields,field_description:l10n_bg_zip.field_res_partner__id", "ID", "ID"),
    ("model:ir.actions.server,name:l10n_bg_zip.ir_cron_relink_partners_ir_actions_server",
     "Bulgaria: link contacts to the city of their ZIP",
     "България: свързване на контактите с населеното място по пощенски код"),
    ("model:ir.actions.server,name:l10n_bg_zip.action_partner_fix_city_from_zip", "Bulgaria: set city from ZIP",
     "България: населено място по пощенски код"),
]  # fmt: skip

PO_HEADER = r"""# Translation of Odoo Server.
# This file contains the translation of the following modules:
# 	* l10n_bg_zip
#
msgid ""
msgstr ""
"Project-Id-Version: Odoo Server 19.0\n"
"Report-Msgid-Bugs-To: \n"
"Last-Translator: \n"
"Language-Team: \n"
"Language: bg\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: \n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
"""

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sht", "ъ": "a",
    "ь": "y", "ю": "yu", "я": "ya",
}  # fmt: skip


def transliterate(text):
    """Official Bulgarian transliteration; "ия" at the end of a word is "ia"."""
    out = []
    lower = text.lower()
    for index, char in enumerate(text):
        low = lower[index]
        if low == "я" and index and lower[index - 1] == "и" and not lower[index + 1 : index + 2].isalpha():
            latin = "a"
        elif low in TRANSLIT:
            latin = TRANSLIT[low]
        else:
            out.append(char)
            continue
        if char != low:
            # capital letter: "Ш" -> "Sh", or "SH" when the whole word is in capitals
            latin = latin.upper() if text.isupper() else latin.capitalize()
        out.append(latin)
    return "".join(out)


def po_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def main(source):
    rows = set()
    with open(source, encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) < 5 or row[0] != "BG":
                continue
            zip_code, place, province = row[1].strip(), row[2].strip(), row[4].strip()
            if not (zip_code and place and province in PROVINCES):
                continue
            cyrillic = place.split(" / ")[0].strip()
            rows.add((zip_code, cyrillic, PROVINCES[province]))
    counter = {}
    with open(ROOT / "data" / "res.city.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["id", "country_id:id", "zipcode", "name", "name@bg_BG", "state_id:id"])
        for zip_code, cyrillic, state in sorted(rows):
            index = counter.get(zip_code, 0)
            counter[zip_code] = index + 1
            latin = transliterate(cyrillic)
            writer.writerow([f"bg_city_{zip_code}_{index}", "base.bg", zip_code, latin, cyrillic, f"state_bg_{state}"])
    lines = [PO_HEADER]
    for reference, source, translation in UI_TRANSLATIONS:
        lines += ["#. module: l10n_bg_zip", f"#: {reference}", f'msgid "{po_escape(source)}"']
        lines += [f'msgstr "{po_escape(translation)}"', ""]
    (ROOT / "i18n" / "bg.po").write_text("\n".join(lines), encoding="utf-8")
    # the template: same entries, untranslated (a translation missing from it is ignored)
    template = [line if not line.startswith('msgstr "') else 'msgstr ""' for line in lines[1:]]
    pot_header = PO_HEADER.replace('"Language: bg\\n"\n', "").replace("nplurals=2; plural=(n != 1);", "")
    (ROOT / "i18n" / "l10n_bg_zip.pot").write_text("\n".join([pot_header] + template), encoding="utf-8")
    xml = [
        '<?xml version="1.0" encoding="utf-8" ?>',
        "<odoo>",
        # the name of a province is not translatable in Odoo: Latin only
        "    <!-- the 28 provinces (oblasti), ISO 3166-2:BG -->",
    ]
    for code, latin, _cyrillic in STATES:
        xml += [
            f'    <record id="state_bg_{code}" model="res.country.state">',
            '        <field name="country_id" ref="base.bg" />',
            f'        <field name="code">{code}</field>',
            f'        <field name="name">{latin}</field>',
            "    </record>",
        ]
    xml += ["</odoo>", ""]
    (ROOT / "data" / "res_country_state_data.xml").write_text("\n".join(xml), encoding="utf-8")
    print(f"{len(rows)} cities written")  # pylint: disable=print-used


if __name__ == "__main__":
    main(sys.argv[1])
