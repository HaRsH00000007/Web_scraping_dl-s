# ============================================================
#  config.py  —  All settings. Only file you need to edit.
# ============================================================

# ---------- Entry DL + DOB (used to reach dlBacklogPublic.do) ----------
ENTRY_DL_NUMBER = "GJ12 20050123456"
ENTRY_DOB       = "01-01-1980"        # DD-MM-YYYY

# ---------- States to scrape ----------
STATES = {
    "Gujarat"       : "GJ",
    "Rajasthan"     : "RJ",
    "Uttar Pradesh" : "UP",
    "Bihar"         : "BR",
}

# ---------- RTO config ----------
MAX_RTO_NUMBER  = 20

# ---------- Numeric Lic No range ----------
MAX_LIC_NUMBER  = 100

# ---------- First Issue Date ----------
FIRST_ISSUE_DATE = "01-01-2005"

# ---------- Paths ----------
OUTPUT_DIR = "output"
LOG_DIR    = "logs"

# ---------- Timing ----------
PAGE_LOAD_WAIT  = 15     # WebDriverWait timeout in seconds
SHORT_DELAY     = 3.0    # delay between lic number iterations
                         # increase to 3.0 or 5.0 if site stops responding
RTO_DELAY       = 3      # delay between RTOs

# ---------- Retry ----------
MAX_RETRIES     = 1

# ---------- Chrome ----------
HEADLESS        = False  # must be False for manual CAPTCHA

# ---------- CAPTCHA ----------
CAPTCHA_MODE    = "manual"