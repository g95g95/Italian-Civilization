# Gaps

Everything the build could not do as the spec asks, with the reason. Each `- ` bullet under
"Open" is also shown in the app's "Rules & sources" panel (scripts/export.py reads this file).

## Open

- The Interior Ministry's open-data files name comuni but carry no ISTAT code. The build bridges them with an exact lookup in ISTAT's register for polling day (scripts/names.py), plus 18 hand-checked spellings in config/name_aliases.csv. This is the only name-based step, and it is a deviation from the rule "joins are on ISTAT codes, never on names". The other datasets (MEF, ISTAT, ISPRA, ASIA) do carry codes and join on them.
- Camera 2022: the Ministry's open-data page says comune-level figures are the unofficial ones sent by comuni, while national totals come from the official proclamations, so the two can differ. Candidate-only votes are also shared among coalition lists at polling-station level, which comune data cannot reproduce exactly. Every list lands within 0.1% of the official national total except the two smallest coalition partners: Noi Moderati (−0.37%) and Impegno Civico (−0.17%). Camera 2018, rebuilt the same way, is within 0.03% for every list.
- No independent national figure is in the Ministry's open data for European 2019, the 2016 referendums or the 2020 referendum: only the comune file exists. For those votes the gate checks that no vote is lost between comuni and tiles, not that the totals match a separate ministry count.
- The section-level files for European 2024 and the 2025 and 2026 referendums are incomplete (for example, whole Sicilian comuni are missing from the 2026 file). They are used only to confirm, comune by comune, the figures of the complete comune-level file.
- Vote from abroad is not on the map (it has no place). National figures in the app are for Italy only.
- Valle d'Aosta elects its deputy in a single-member contest with local symbols. Its Camera tiles show turnout and candidate shares but no ideology score. European elections and referendums cover Valle d'Aosta normally.
- European 2019: the +Europa list (+Europa, Italia in Comune, PDE) and Europa Verde have no score, because the 2019 survey wave rated neither party; together they hold 5.4% of valid votes. Radicali Italiani is scored but was not a party on that symbol. In the 2018 Camera vote, +Europa was a joint list that included Radicali Italiani, so it takes that party's score. This choice changes what the 2019 number means and should be confirmed.
- CORINE Land Cover 2018 could not be downloaded: every EEA host failed through this environment's proxy. Land cover uses the JRC LUISA Base Map 2018, a 100 m refinement of CORINE 2018 that keeps the CORINE class codes.
- Elevation uses TINITALY 1.1 sampled at 250 m through INGV's coverage service, not the full 10 m grid (several GB). Means over 10 km tiles are unaffected; single peaks come out slightly low.
- Universities: the MUR open-data portal (dati-ustat.mur.gov.it) did not answer through the proxy, so the Wonders layer has UNESCO sites and ports only.
- UNESCO: the official list endpoints sit behind a bot challenge. Sites come from UNESCO's 2023 export (GitHub mirror), so the three Italian sites inscribed since 2023 are missing, and four cross-border sites whose reference point lies abroad have no tile.
- Labour-market areas: ISTAT published a 2021 delineation (515 areas) in October 2025, but its comune-to-area table is only on SITUAS, which this environment could not query for it. Cities use the 2011 delineation (610 areas, composition at 1 January 2023), which ISTAT publishes as a coded table.
- Population grid: 504 residents in census-grid cells that touch no comune polygon (border and coast mismatches between the two ISTAT products) are not on any tile.
- Territory transfers between comuni that did not change any code (frazioni moving from one comune to another) are not modelled: results follow the comune as it was on polling day.
