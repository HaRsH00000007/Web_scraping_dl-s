# ============================================================
#  scraper.py — Fills number, YOU click blank area, script captures popup
# ============================================================

import os
import time
import logging
import re
from typing import Optional, Dict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, UnexpectedAlertPresentException,
    NoSuchElementException
)
from webdriver_manager.chrome import ChromeDriverManager

from excel_handler import append_row

logger = logging.getLogger("sarathi")
os.environ["WDM_LOCAL"] = "1"
os.environ["WDM_LOG"]   = "0"


def create_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)

    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if "sarathi" in driver.current_url.lower() or \
           "parivahan" in driver.current_url.lower():
            logger.info(f"Connected: {driver.current_url}")
            return driver

    logger.warning(f"Using active tab: {driver.current_url}")
    return driver


def _find_lic_field(driver):
    result = driver.execute_script("""
        var inputs = document.querySelectorAll('input');
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            var name = (el.name || '').toLowerCase();
            var id   = (el.id   || '').toLowerCase();
            var ph   = (el.placeholder || '').toLowerCase();
            if (name.includes('numeric') || id.includes('numeric') ||
                ph.includes('part of the original') ||
                name.includes('licno') || id.includes('licno')) {
                return el;
            }
        }
        return null;
    """)
    return result


def auto_fill_and_capture(driver, output_path, state_name, start, logger):
    """
    Script fills the Numeric Lic No field automatically.
    YOU click blank area to trigger popup.
    Script captures popup and moves to next number.
    """
    saved   = 0
    current = start

    time.sleep(1)
    print(f"\n  Filling Numeric Lic No automatically from {start}.")
    print("  YOUR JOB: After each number appears in field → click blank area on page.")
    print("  Script will capture the popup and fill next number automatically.")
    print("  Press Ctrl+C to stop.\n")

    while True:
        # Check browser alive
        try:
            _ = driver.current_url
        except WebDriverException:
            logger.info("Browser closed.")
            break

        try:
            # Find and fill the field
            field = _find_lic_field(driver)
            if not field:
                print(f"  Waiting for Numeric Lic No field...")
                time.sleep(2)
                continue

            # Clear field first, wait, then fill — avoids rate limiting
            driver.execute_script("""
                var el = arguments[0];
                el.value = '';
                el.dispatchEvent(new Event('input',  {bubbles:true}));
                el.dispatchEvent(new Event('change', {bubbles:true}));
            """, field)
            time.sleep(1.5)  # pause before filling next number

            # Now fill the number
            driver.execute_script("""
                var el = arguments[0];
                el.focus();
                el.value = arguments[1];
                el.dispatchEvent(new Event('input',  {bubbles:true}));
                el.dispatchEvent(new Event('change', {bubbles:true}));
            """, field, str(current))

            print(f"  >> Filled #{current} — now click blank area on page...")

            # Wait for alert — up to 40 seconds
            alert_found = False
            for _ in range(5):   # check every 2 seconds, 10s max per number
                try:
                    WebDriverWait(driver, 2).until(EC.alert_is_present())
                    alert_found = True
                    break
                except TimeoutException:
                    continue

            if not alert_found:
                print(f"  #{current} — no record found, skipping.")
                current += 1
                continue

            # Handle alert
            alert = driver.switch_to.alert
            text  = alert.text

            # SCOSTA dialog → click OK → wait for details popup
            if "licence already issued" in text.lower() or \
               "do you want to generate" in text.lower():
                alert.accept()
                # Now wait for the details popup
                try:
                    WebDriverWait(driver, 5).until(EC.alert_is_present())
                    alert = driver.switch_to.alert
                    text  = alert.text
                    alert.accept()
                except TimeoutException:
                    current += 1
                    continue

            else:
                alert.accept()

            # Parse and save
            data = _parse_alert(text, state_name)
            if data:
                append_row(output_path, data, logger)
                saved += 1
                print(
                    f"  [{saved}] #{current} → "
                    f"{data['DL Number']} | {data['Name']} | {data['Date of Birth']}"
                )
            else:
                logger.debug(f"#{current} skipped: {text[:60]}")

            current += 1

        except KeyboardInterrupt:
            print(f"\n  Stopped at #{current}. {saved} records saved.")
            break

        except UnexpectedAlertPresentException:
            try:
                alert = driver.switch_to.alert
                text  = alert.text
                if "licence already issued" in text.lower() or \
                   "do you want to generate" in text.lower():
                    alert.accept()
                else:
                    alert.accept()
                    data = _parse_alert(text, state_name)
                    if data:
                        append_row(output_path, data, logger)
                        saved += 1
                        print(f"  [{saved}] #{current} → {data['DL Number']} | {data['Name']}")
            except Exception:
                pass
            current += 1

        except Exception as e:
            logger.warning(f"#{current} error: {e}")
            try:
                driver.switch_to.alert.accept()
            except Exception:
                pass
            current += 1
            time.sleep(1)

    return saved


def _parse_alert(text, state_name):
    if not text:
        return None
    for kw in ["not available", "central repository", "concern rto",
                "invalid", "incorrect", "please enter", "error",
                "no record", "not found", "try again",
                "licence already issued", "do you want"]:
        if kw in text.lower():
            return None
    if "DL Number" not in text:
        return None

    def get(pattern):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    dl   = get(r"DL Number[:\s]+(.+)")
    name = get(r"Name[:\s]+(.+)")
    if not dl or not name:
        return None

    return {
        "DL Number"     : dl,
        "Name"          : name,
        "Date of Birth" : get(r"Date of Birth[:\s]+(.+)"),
        "Application No": get(r"Application Number[:\s]+(.+)"),
        "State"         : state_name,
        "RTO"           : "",
    }