# MEF – Dipartimento delle Finanze: Redditi e principali variabili IRPEF su base comunale

Download date: 2026-11-27 (files saved unmodified).

## Files

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip` | 1,028,668 | 75cecc95d72b76cda545666154e95ab414df1983f8a0eeef72915862ef4e8cb7 |

Archive contents: `Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.csv` (2,313,404 bytes, 7,898 lines incl. header).

- Download URL: https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800
- Index page: https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?search_class%5B0%5D=cCOMUNE&opendata=yes
- Publisher: Ministero dell'Economia e delle Finanze, Dipartimento delle Finanze (statistiche fiscali, open data).
- Licence as stated on the index page ("Tipo licenza"): Creative Commons Attribution 3.0 Italy (CC BY 3.0 IT), http://creativecommons.org/licenses/by/3.0/it/
- Vintage: **anno d'imposta 2024** (dichiarazioni presentate nel 2025; the page labels it "2025 a.i. 2024"), published 23 April 2026. This is the latest comune-level year on the index (older years 2012–2023 also listed).

## Format

- CSV, separator `;`, CRLF line endings, ASCII/Latin-1 text, no quoting. Header line has a trailing `;` (53 header fields vs 52 data fields).
- Amounts are integers in euro; "Frequenza" = number of taxpayers with that item.
- One row per comune (7,896 comuni) plus one residual row with `Codice Istat Comune` = `0`, `Regione` = `Mancante/errata` (5,305 taxpayers whose comune is missing/wrong).

## Comune code

`Codice Istat Comune` is the 6-digit ISTAT code as a zero-padded string (e.g. `001272` = TORINO), matching PRO_COM_T directly when read as text. `Codice catastale` is the Belfiore code (e.g. L219). Codes are those valid in the tax year (territorial changes after 2024 are not applied).

## Columns (in order)

1 Anno di imposta · 2 Codice catastale · 3 Codice Istat Comune · 4 Denominazione Comune · 5 Sigla Provincia · 6 Regione · 7 Codice Istat Regione · 8 **Numero contribuenti** ·
then pairs "<item> - Frequenza" / "<item> - Ammontare in euro" for items:
Reddito da fabbricati; Reddito da lavoro dipendente e assimilati; Reddito da pensione; Reddito da lavoro autonomo (comprensivo dei valori nulli); Reddito di spettanza dell'imprenditore in contabilita' ordinaria (comprensivo dei valori nulli); ... in contabilita' semplificata (...); Reddito da partecipazione (...); **Reddito imponibile** (cols 23–24); Imposta netta; Trattamento spettante; Reddito imponibile addizionale; Addizionale regionale dovuta; Addizionale comunale dovuta; **Reddito complessivo** (cols 35–36); Reddito complessivo by class: <=0, 0–10000, 10000–15000, 15000–26000, 26000–55000, 55000–75000, 75000–120000, oltre 120000 euro (cols 37–52).

Note: some column names contain double spaces (e.g. `Reddito da partecipazione  (comprensivo dei valori nulli) - Frequenza`); match them exactly.

## Reference totals (computed from the file, all rows incl. the residual row)

- Numero contribuenti: 42,837,963 (residual row: 5,305)
- Reddito imponibile – Ammontare: 1,013,394,277,109 EUR (frequency 40,709,947; residual row 59,360,581 EUR)
- Reddito complessivo – Ammontare: 1,076,317,631,327 EUR
- Torino (001272): 643,012 contribuenti; reddito imponibile 17,490,525,903 EUR
