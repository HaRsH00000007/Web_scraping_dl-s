# ============================================================
#  main.py  —  Run: python main.py
# ============================================================

import time
from logger        import setup_logger
from excel_handler import get_output_path, init_output_file
from scraper       import create_driver, auto_fill_and_capture


def main():
    logger = setup_logger()

    print("\n" + "="*60)
    print("  Sarathi DL Scraper — Auto Fill Mode")
    print("="*60)
    print("""
  STEP 1: Launch Chrome with debugging (run launch_chrome.bat)

  STEP 2: In that Chrome, manually:
    - Select state → DL Services → Continue
    - Enter DL + DOB + CAPTCHA
    - On Backlog page: fill Apply to State, RTO, First Issue Date

  STEP 3: Come back here and press Enter
    """)

    input("  Press Enter when you are on the DL Backlog page: ")

    state_name = input("  Enter state name (e.g. Gujarat): ").strip()
    if not state_name:
        state_name = "output"

    start_num = input("  Start from Lic No (default 1): ").strip()
    start_num = int(start_num) if start_num.isdigit() else 1

    output_path = get_output_path(state_name)
    init_output_file(output_path, logger)

    print("\n  Connecting to Chrome...")
    try:
        driver = create_driver()
    except Exception as e:
        print(f"\n  ERROR connecting to Chrome: {e}")
        print("  Make sure launch_chrome.bat was used to open Chrome.")
        return

    print(f"  Connected! Output: {output_path}")

    saved = auto_fill_and_capture(
        driver, output_path, state_name, start_num, logger
    )

    print(f"\n  Done. {saved} total records saved to {output_path}")
    logger.info(f"Complete. {saved} records saved.")


if __name__ == "__main__":
    main()