Loads the 28 Bulgarian provinces (oblasti) and the Bulgarian localities with their postal
code, and fills in the city and the province of Bulgarian addresses from the postal code.

- Creates the 28 provinces with their ISO 3166-2:BG code. Provinces already entered by hand
  (in Latin or in Cyrillic, with or without "Province") are reused and their duplicates
  merged, so the database does not get a second set.
- Ships the list of Bulgarian localities with their postal code, from
  [GeoNames](https://www.geonames.org) (Creative Commons Attribution 4.0). The names are in
  Latin, with the official Bulgarian transliteration (Haskovo, Vratsa, Targovishte); the
  Cyrillic names are the Bulgarian translation, shown to the users working in Bulgarian.
- Bulgaria is set to *enforce cities*: the city of a Bulgarian address is chosen from the list.
- On the contact form, typing the postal code of a Bulgarian address sets the city and the
  province. A postal code shared by several localities sets only the province; the city name,
  when it matches one of them (in Latin or in Cyrillic, without accents and case), picks the
  locality. A "BG-" prefix is dropped.
- The action *Bulgaria: set city from ZIP* on contacts links the Bulgarian contacts to the
  city of their postal code and fills in the province.
- At install, the Bulgarian contacts are linked: directly on a small database, by the
  scheduled action *Bulgaria: link contacts to the city of their ZIP* in batches on a large
  one (it deactivates itself when done).
- Every form that runs the postal code rules of the contact (for example the delivery details
  of an AWB, with `deltatech_delivery`) gets the city and the province filled in.
