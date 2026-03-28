# Sarathi DL Scraper

A two-phase Python + Selenium automation tool that extracts driving licence data from the Indian government's Sarathi Parivahan portal and enriches it with full profile details from idcard.store.

---

## Project Structure

```
Web_scraper/
├── main.py              # Phase 1 entry point
├── phase2.py            # Phase 2 entry point
├── scraper.py           # Selenium logic (popup capture, auto-fill)
├── config.py            # All settings (DL, DOB, delays, paths)
├── excel_handler.py     # Crash-safe Excel read/write
├── logger.py            # File + console logging
├── requirements.txt     # Python dependencies
├── output/              # All Excel output files
└── logs/                # Run logs with timestamps
```

---

## How It Works

### Phase 1 — Sarathi Backlog Scraper

**Goal:** Extract DL Numbers, Names, DOBs, and Application Numbers from the Sarathi government portal.

**The exploit:** On the DL Backlog Data Entry page (`dlBacklogPublic.do`), there is a field called **Numeric Lic No**. Entering any number (1, 2, 3...) and clicking blank area triggers a JavaScript `alert()` popup containing real DL holder details from the government database. Each number returns a different person's record for that RTO.

**Website flow:**

```
sarathi.parivahan.gov.in/sarathiservice/stateSelection.do
  → Close "Update Mobile Number" popup
  → Select state from dropdown
  → Click: Driving Licence → Services On DL (Renewal/Duplicate/AEDL/IDP/Others)
  → Click: Continue
  → envaction.do: Enter real DL + DOB + CAPTCHA → Click "Get DL Details"
  → dlBacklogPublic.do: Fill Apply to State, Apply to RTO, First Issue Date
  → Enter Numeric Lic No (1, 2, 3...) → popup fires with DL holder details
  → Script captures popup → saves to Excel → next number
```

**What the script does:**
- Opens Chrome with remote debugging (port 9222) and attaches to your existing session
- You navigate manually to the Backlog page and fill the form fields
- Script auto-fills the Numeric Lic No field (1, 2, 3...) every cycle
- You click the blank area on the page to trigger each popup
- Script captures the popup text, parses the DL data, and writes it to Excel instantly
- Numbers with no records (empty popups) are skipped after 10 seconds
- Press Ctrl+C at any time — all records already saved

**Output columns:** `DL Number | Name | Date of Birth | Application No | State | RTO`

**Key technical details:**
- Chrome is launched with `--remote-debugging-port=9222` and `--user-data-dir=C:\Temp\chromedbg` for a separate, clean session
- Script connects to Chrome via `debuggerAddress: 127.0.0.1:9222`
- Numeric Lic No field is filled via JavaScript `nativeInputValueSetter` to trigger React state updates
- Alert popups are captured using `WebDriverWait(driver, 10).until(EC.alert_is_present())`
- The "Licence Already Issued" SCOSTA confirm dialog is handled automatically (clicks OK)
- Excel is written row-by-row (crash-safe) using openpyxl

---

### Phase 2 — DL Profile Enricher (idcard.store)

**Goal:** Take the Phase 1 Excel and fetch full DL profile details for each record.

**How it works:** The website `idcard.store` provides a free DL lookup service. You enter a DL number and DOB, and it returns a complete profile card including photo, address, mobile number, vehicle class, and validity dates — all sourced from the government database, no CAPTCHA required.

**Flow:**

```
POST https://api.idcard.store/free/free_dl
  payload: { relation: "DL No", dl: "GJ01 20120000002", dob: "27-07-1991" }
  headers: { Authorization: "Bearer <token>" }
  
  → Response: { cards: [{ html: "2026-03-14/uuid.html" }] }
  
  → Selenium fetches: https://idmaker.mfcdn.in/2026-03-14/uuid.html
  → BeautifulSoup parses all table rows
  → All fields extracted and saved to Excel
```

**What the script does:**
- Reads every DL Number + DOB from the Phase 1 Excel file
- Converts DOB format automatically (YYYY-MM-DD → DD-MM-YYYY)
- POSTs to the idcard.store API to get the HTML card URL
- Uses Selenium (your Chrome session) to fetch the card from `idmaker.mfcdn.in` CDN — bypasses Cloudflare
- Parses all fields using BeautifulSoup
- Retries up to 4 times if the CDN page is not ready yet
- Already-processed records are skipped on re-run (resume-safe)
- Saves row-by-row to Excel

**Output columns:**
```
DL Number | Name | Son/Daughter/Wife of | Date of Birth | Present Address |
Mobile Number | Initial Issue Date | Initial Issuing Office |
Last Endorsed Date | Last Endorsed Office | Last Completed Transaction |
Non-Transport From | Non-Transport To | Transport From | Transport To |
COV Category | Class of Vehicle | COV Issue Date | Photo URL | Status
```

**Key technical details:**
- API endpoint: `https://api.idcard.store/free/free_dl` (POST, multipart/form-data)
- HTML cards hosted on CDN: `https://idmaker.mfcdn.in/<date>/<uuid>.html`
- Auth token is a Bearer token from your idcard.store session (update in `phase2.py` when it expires)
- DOB normalisation handles: `YYYY-MM-DD`, `DD-MM-YYYY`, `DD/MM/YYYY`
- `Status` column: `OK`, `NO_DATA`, `NO_CARD`, `AUTH_EXPIRED`, `API_4xx`, `NO_TABLE`

---

## Running the Project

### Requirements

```bash
pip install selenium webdriver-manager openpyxl beautifulsoup4 requests
```

### Phase 1

```bash
# Step 1 — Kill any existing Chrome
taskkill /F /IM chrome.exe /T

# Step 2 — Launch Chrome with remote debugging
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--user-data-dir=C:\Temp\chromedbg"

# Step 3 — Run Phase 1
python main.py
```

Then manually navigate to the Sarathi Backlog page in that Chrome window and start entering Numeric Lic Nos.

### Phase 2

```bash
# Step 1 — Kill any existing Chrome
taskkill /F /IM chrome.exe /T

# Step 2 — Launch Chrome with remote debugging
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--user-data-dir=C:\Temp\chromedbg"

# Step 3 — Run Phase 2
python phase2.py
```

Log in to idcard.store in the Chrome window, navigate to `idcard.store/u/free/driving_licence`, then enter the Phase 1 Excel path when prompted.

---

## Configuration

Edit `config.py` to change settings:

| Setting | Default | Description |
|---|---|---|
| `ENTRY_DL_NUMBER` | `GJ12 20050123456` | DL used to reach the backlog page |
| `ENTRY_DOB` | `01-01-1980` | DOB matching the entry DL |
| `SHORT_DELAY` | `3.0` | Seconds between Lic No fills (increase if site rate-limits) |
| `MAX_LIC_NUMBER` | `100` | Max Lic Nos to try per RTO |
| `OUTPUT_DIR` | `output` | Folder for Excel output files |

Edit `phase2.py` to update the auth token:

```python
AUTH_TOKEN = "Bearer <your-token-here>"
```

To get a fresh token: log in to idcard.store → F12 → Network tab → submit any DL → click the `free_dl` request → Headers → copy the `Authorization` value.

---

## Challenges Solved

| Problem | Solution |
|---|---|
| Selenium Chrome had no internet (`ERR_ADDRESS_UNREACHABLE`) | Switched to attaching to user's own Chrome via remote debugging port |
| Site blocks right-click, F12, keyboard shortcuts | Used JavaScript injection to fill fields and trigger events |
| Numeric Lic No field not triggering popup | Discovered site requires a click on blank area after filling — made semi-manual |
| React inputs not updating from Selenium | Used `nativeInputValueSetter` via JS to properly trigger React's synthetic events |
| idcard.store HTML blocked by Cloudflare (403) | HTML is served from separate CDN (`idmaker.mfcdn.in`) which has no Cloudflare |
| CDN HTML not ready immediately after API call | Added 4-attempt retry with `WebDriverWait` for table element |
| Site rate-limits after ~10 rapid requests | Added configurable `SHORT_DELAY` between fills |
| SCOSTA "Licence Already Issued" confirm dialog | Handled automatically — script clicks OK and waits for details popup |

---

## Notes

- Phase 1 requires one valid DL + DOB per state to pass the `envaction.do` gate
- The idcard.store auth token expires with the browser session — update `AUTH_TOKEN` in `phase2.py` after re-login
- Both phases are resume-safe — re-run will skip already-processed records
- All output files are timestamped to avoid overwrites
