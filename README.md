# l10n-bulgaria

Localizare Odoo pentru Bulgaria (Terrabit).

## Module

- `l10n_bg_zip` — cele 28 de regiuni ale Bulgariei (ISO 3166-2:BG) și localitățile cu codul
  poștal; completează localitatea și regiunea din codul poștal și leagă contactele existente
  de localitatea codului lor poștal: la instalare, direct pe o bază mică sau printr-o acțiune
  programată, pe loturi, pe una mare. Regiunile deja introduse de mână sunt preluate, fără
  dubluri. Numele sunt în latină (transliterarea oficială); varianta chirilică a localităților
  e în coloana `name@bg_BG` din `data/res.city.csv`, încărcată ca traducere bulgară.

## Date

Lista de localități vine din [GeoNames](https://www.geonames.org) (licență Creative Commons
Attribution 4.0). Pentru reîmprospătare (regenerează și regiunile, `i18n/bg.po` și
`l10n_bg_zip.pot`):

```bash
curl -sSfLO https://download.geonames.org/export/zip/BG.zip && unzip BG.zip BG.txt
python3 scripts/generate_city_data.py BG.txt
```
