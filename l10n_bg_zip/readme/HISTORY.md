## 19.0.1.0.1 (2026-11-04)

**Changed**

- The Cyrillic names of the localities are in the column `name@bg_BG` of
  `data/res.city.csv`, loaded by Odoo as the Bulgarian translation; `bg.po` keeps only the
  interface strings. The provinces stay in Latin: their name is not translatable in Odoo.

## 19.0.1.0.0 (2026-11-04)

**Added**

- The 28 Bulgarian provinces (ISO 3166-2:BG), reusing the provinces already in the database.
- Bulgarian localities with postal code, from GeoNames, named in Latin with the Cyrillic
  names as Bulgarian translation.
- City and province filled in from the postal code on Bulgarian addresses; action and
  scheduled action to link the existing contacts.
- Consultant sheet (readme/FISA_CONSULTANT.md) and screenshots, in Romanian and English.
