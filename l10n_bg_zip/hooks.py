# ©  2026 Terrabit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging
import re
import unicodedata

from odoo.tools import SQL

from .models.res_partner import RELINK_BATCH

_logger = logging.getLogger(__name__)

# xml id, name in Latin, name in Cyrillic, as loaded by data/res_country_state_data.xml
PROVINCES = [
    ("state_bg_01", "Blagoevgrad", "Благоевград"),
    ("state_bg_02", "Burgas", "Бургас"),
    ("state_bg_03", "Varna", "Варна"),
    ("state_bg_04", "Veliko Tarnovo", "Велико Търново"),
    ("state_bg_05", "Vidin", "Видин"),
    ("state_bg_06", "Vratsa", "Враца"),
    ("state_bg_07", "Gabrovo", "Габрово"),
    ("state_bg_08", "Dobrich", "Добрич"),
    ("state_bg_09", "Kardzhali", "Кърджали"),
    ("state_bg_10", "Kyustendil", "Кюстендил"),
    ("state_bg_11", "Lovech", "Ловеч"),
    ("state_bg_12", "Montana", "Монтана"),
    ("state_bg_13", "Pazardzhik", "Пазарджик"),
    ("state_bg_14", "Pernik", "Перник"),
    ("state_bg_15", "Pleven", "Плевен"),
    ("state_bg_16", "Plovdiv", "Пловдив"),
    ("state_bg_17", "Razgrad", "Разград"),
    ("state_bg_18", "Ruse", "Русе"),
    ("state_bg_19", "Silistra", "Силистра"),
    ("state_bg_20", "Sliven", "Сливен"),
    ("state_bg_21", "Smolyan", "Смолян"),
    ("state_bg_22", "Sofia City", "София (столица)"),
    ("state_bg_23", "Sofia", "София"),
    ("state_bg_24", "Stara Zagora", "Стара Загора"),
    ("state_bg_25", "Targovishte", "Търговище"),
    ("state_bg_26", "Haskovo", "Хасково"),
    ("state_bg_27", "Shumen", "Шумен"),
    ("state_bg_28", "Yambol", "Ямбол"),
]

# other spellings found in databases where the provinces were entered by hand
ALIASES = {
    "state_bg_22": ["sofia grad", "sofia capital", "sofiya grad", "grad sofia", "sofia stolitsa", "sofia stolica"],
    "state_bg_23": ["sofiya"],
    "state_bg_06": ["vraca"],
    "state_bg_09": ["kurdzhali", "kardjali"],
    "state_bg_10": ["kjustendil"],
    "state_bg_21": ["smoljan"],
    "state_bg_25": ["turgovishhe", "targovishte province"],
    "state_bg_26": ["khaskovo", "hasskovo"],
    "state_bg_28": ["jambol"],
}


def _normalize(name):
    name = unicodedata.normalize("NFKD", name or "")
    name = "".join(c for c in name if not unicodedata.combining(c)).casefold()
    # "Sofia Province" is "Sofia", "Sofia City Province" is "Sofia City"
    name = re.sub(r"\b(province|oblast|област|region)\b", " ", name)
    return " ".join(re.sub(r"[^\w]+", " ", name).split())


def _names(xml_id, latin, cyrillic):
    return {_normalize(latin), _normalize(cyrillic)} | {_normalize(a) for a in ALIASES.get(xml_id, [])}


def _state_references(env):
    """Stored many2one columns pointing to res.country.state, as (table, column)."""
    fields = (
        env["ir.model.fields"]
        .sudo()
        .search([("relation", "=", "res.country.state"), ("ttype", "=", "many2one"), ("store", "=", True)])
    )
    references = []
    for field in fields:
        model = env.get(field.model)
        if model is None or model._abstract or not model._auto or field.name not in model._fields:
            continue
        if not model._fields[field.name].store or model._fields[field.name].company_dependent:
            continue
        references.append((model._table, field.name))
    return references


def _usage(env, references, state_id):
    total = 0
    for table, column in references:
        env.cr.execute(
            SQL("SELECT COUNT(*) FROM %s WHERE %s = %s", SQL.identifier(table), SQL.identifier(column), state_id)
        )
        total += env.cr.fetchone()[0]
    return total


def _adopt_existing_provinces(env):
    """Reuse the Bulgarian provinces already in the database.

    Without it, a database where the provinces were entered by hand gets a second
    copy of each. For every province of the module, the most used existing province
    of the same name (in Latin or in Cyrillic) gets the xml id of the module, so that
    loading the data updates it; its duplicates are merged into it.
    """
    bulgaria = env.ref("base.bg", raise_if_not_found=False)
    if not bulgaria:
        return
    states = env["res.country.state"].with_context(active_test=False).search([("country_id", "=", bulgaria.id)])
    if not states:
        return
    references = _state_references(env)
    data = env["ir.model.data"].sudo()
    for xml_id, latin, cyrillic in PROVINCES:
        if data.search_count([("module", "=", "l10n_bg_zip"), ("name", "=", xml_id)]):
            continue
        names = _names(xml_id, latin, cyrillic)
        candidates = states.filtered(lambda s, n=names: _normalize(s.name) in n)
        if not candidates:
            continue
        keep = max(candidates, key=lambda s: (_usage(env, references, s.id), -s.id))
        for duplicate in candidates - keep:
            for table, column in references:
                env.cr.execute(
                    SQL(
                        "UPDATE %s SET %s = %s WHERE %s = %s",
                        SQL.identifier(table),
                        SQL.identifier(column),
                        keep.id,
                        SQL.identifier(column),
                        duplicate.id,
                    )
                )
            _logger.info("l10n_bg_zip: province %s (id %s) merged into id %s", duplicate.name, duplicate.id, keep.id)
        env.invalidate_all()
        (candidates - keep).unlink()
        data.create({"module": "l10n_bg_zip", "name": xml_id, "model": "res.country.state", "res_id": keep.id})
        _logger.info("l10n_bg_zip: existing province %s (id %s) reused as %s", keep.name, keep.id, xml_id)
        states -= candidates


def pre_init_hook(env):
    _adopt_existing_provinces(env)


def post_init_hook(env):
    # link the Bulgarian contacts to the city of their postal code; a large database
    # is left to the cron, in batches, so that the install does not time out
    Partner = env["res.partner"].with_context(active_test=False)
    domain = Partner._l10n_bg_relink_domain()
    if Partner.search_count(domain) <= RELINK_BATCH:
        Partner._l10n_bg_relink_batch(0)
        return
    cron = env.ref("l10n_bg_zip.ir_cron_relink_partners")
    cron.active = True
    cron._trigger()
