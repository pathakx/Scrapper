# Shoalhaven DA Tracking Web Scraper - FINAL COMPLETE VERSION
# Collects DA + Full URLs, then scrapes sequentially with cleaning rules
# Install dependencies: pip install selenium webdriver-manager beautifulsoup4 pandas

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException,
    InvalidArgumentException
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import re


# ==================== CONFIGURATION ====================
START_DATE = "01/09/2025"
END_DATE = "30/09/2025"
BASE_URL = "https://www3.shoalhaven.nsw.gov.au/masterviewUI/modules/ApplicationMaster/Default.aspx"
BASE_APP = "https://www3.shoalhaven.nsw.gov.au/masterviewUI/modules/ApplicationMaster/"
BASE_ROOT = "https://www3.shoalhaven.nsw.gov.au"
OUTPUT_CSV = "results.csv"
WAIT_TIME = 20
# =====================================================


# EXACT text for cleaning rules
FEES_NO_FEES_TEXT = "No fees recorded against this application."
CONTACT_NO_EXHIBITION_TEXT = "Application Is Not on exhibition, please call Council on 1300 293 111 if you require assistance."


# CSV headers (EXACT order and spelling)
HEADERS = [
    "DA_Number",
    "Detail_URL",
    "Description",
    "Submitted_Date",
    "Decision",
    "Categories",
    "Property_Address",
    "Applicant",
    "Progress",
    "Fees",
    "Documents",
    "Contact_Council",
]


# ==================== DRIVER INITIALIZATION ====================

def create_driver(headless=False):
    """Create and configure Chrome WebDriver."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver


# ==================== STEPS 1-4: SETUP & SEARCH ====================

def step_1_accept_disclaimer(driver):
    """STEP 1: Accept terms and conditions."""
    print("\n" + "="*70)
    print("STEP 1: Accept Disclaimer")
    print("="*70)
    
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, WAIT_TIME)
    
    try:
        agree_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Agree']"))
        )
        agree_btn.click()
        time.sleep(2)
        print("✅ Clicked 'Agree' button")
        return True
    except Exception as e:
        print(f"⚠️  Agree button not found: {e}")
        return True


def step_2_navigate_da_tracking(driver):
    """STEP 2: Navigate to DA Tracking module."""
    print("\n" + "="*70)
    print("STEP 2: Navigate to DA Tracking")
    print("="*70)
    
    wait = WebDriverWait(driver, WAIT_TIME)
    try:
        da_link = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[.//span[text()='DA Tracking']]")
            )
        )
        da_link.click()
        print("✅ Navigated to DA Tracking")
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def step_3_open_advanced_search(driver):
    """STEP 3: Open Advanced Search panel."""
    print("\n" + "="*70)
    print("STEP 3: Open Advanced Search")
    print("="*70)
    
    wait = WebDriverWait(driver, WAIT_TIME)
    try:
        time.sleep(2)
        adv_search = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[.//span[text()='Advanced Search']]")
            )
        )
        driver.execute_script("arguments[0].click();", adv_search)
        print("✅ Opened Advanced Search panel")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def step_4_set_date_range(driver, start_date, end_date):
    """STEP 4: Set date range."""
    print("\n" + "="*70)
    print("STEP 4: Set Date Range")
    print("="*70)
    
    wait = WebDriverWait(driver, WAIT_TIME)
    try:
        time.sleep(1)
        
        from_input = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[contains(@id,'ctl03_dateInput')]")
            )
        )
        to_input = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[contains(@id,'ctl05_dateInput')]")
            )
        )
        
        # Set FROM date
        from_input.click()
        time.sleep(0.3)
        from_input.clear()
        time.sleep(0.3)
        for char in start_date:
            from_input.send_keys(char)
            time.sleep(0.05)
        from_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        # Set TO date
        to_input.click()
        time.sleep(0.3)
        to_input.clear()
        time.sleep(0.3)
        for char in end_date:
            to_input.send_keys(char)
            time.sleep(0.05)
        to_input.send_keys(Keys.TAB)
        time.sleep(0.5)
        
        print(f"✅ Date range set: {start_date} → {end_date}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def step_4b_click_search(driver):
    """STEP 4B: Click Search button."""
    print("\n" + "="*70)
    print("STEP 4B: Click Search")
    print("="*70)
    
    wait = WebDriverWait(driver, WAIT_TIME)
    try:
        search_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "ctl00_cphContent_ctl00_btnSearch"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
        time.sleep(0.5)
        search_btn.click()
        print("✅ Clicked Search button")

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//table[contains(@class,'rgMasterTable')] | //span[contains(text(),'No records')]")
            )
        )
        time.sleep(2)
        print("✅ Results grid loaded")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


# ==================== EXTRACT PAGES & ITEMS ====================

def extract_total_pages_and_items(driver):
    """Extract total pages and items from rgInfoPart div."""
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        info_div = soup.find("div", {"class": re.compile(r"rgWrap.*rgInfoPart")})
        
        if not info_div:
            print("⚠️  Could not find rgInfoPart div")
            return None, None
        
        strong_tags = info_div.find_all("strong")
        
        if len(strong_tags) >= 2:
            total_items = int(strong_tags[0].get_text(strip=True))
            total_pages = int(strong_tags[1].get_text(strip=True))
            return total_items, total_pages
        
        return None, None
    except Exception as e:
        print(f"❌ Error extracting pages: {e}")
        return None, None


# ==================== URL NORMALIZATION ====================

def normalize_url(raw_url):
    """
    Normalize relative URLs to absolute URLs.
    Handles: default.aspx?..., /path, https://...
    """
    if not raw_url:
        return ""
    
    url = raw_url.strip()
    
    # Already absolute
    if url.lower().startswith(("http://", "https://")):
        return url
    
    # Relative to ApplicationMaster directory
    if url.startswith("default.aspx"):
        return BASE_APP + url
    
    # Site-root relative
    if url.startswith("/"):
        return BASE_ROOT + url
    
    # Default: assume ApplicationMaster-relative
    return BASE_APP + url


# ==================== STEP 5: COLLECT DA + FULL URLs ====================

def parse_row_link_href(row):
    """Extract href value from Show button link."""
    a = row.find("a")
    if not a:
        return None
    
    href = (a.get("href") or "").strip()
    
    # Skip javascript: links (postbacks)
    if href.lower().startswith("javascript:"):
        return None
    
    return href


def collect_da_and_urls(driver, total_pages):
    """
    Collect DA numbers and normalized full URLs from all pages.
    Returns: [{'da': str, 'url': str}, ...]
    """
    results = []
    seen_das = set()  # Track DAs to prevent duplicates
    page_num = 1
    
    print("\n" + "="*70)
    print("STEP 5: Collecting DA Numbers + Full URLs")
    print("="*70)
    print(f"Total pages to process: {total_pages}\n")
    
    while page_num <= total_pages:
        print(f"📄 Page {page_num}/{total_pages}: Collecting...", end=" ")
        
        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table", {"class": re.compile("rgMasterTable")})
            
            if not table:
                print("⚠️  Table not found")
                break
            
            rows = table.find_all("tr")[1:]  # Skip header
            page_count = 0
            
            for row in rows:
                cells = row.find_all("td")
                show_img = row.find("img", {"src": re.compile("GridShowButton\.png")})
                
                if not show_img or len(cells) < 2:
                    continue
                
                da = cells[1].get_text(strip=True)
                
                # Skip duplicates
                if da in seen_das:
                    continue
                
                href = parse_row_link_href(row)
                if not href:
                    continue
                
                full_url = normalize_url(href)
                
                results.append({
                    "da": da,
                    "url": full_url
                })
                seen_das.add(da)
                page_count += 1
            
            print(f"✅ {page_count} unique (Total: {len(results)})")
            
            # Stop if last page
            if page_num == total_pages:
                print(f"\n{'='*70}")
                print(f"🛑 Reached last page ({page_num}/{total_pages})")
                print(f"{'='*70}")
                print(f"✅ Collection Complete: {len(results)} unique DAs")
                print(f"{'='*70}\n")
                break
            
            # Go to next page
            try:
                next_btn = driver.find_element(
                    By.XPATH, 
                    "//input[@class='rgPageNext'][@type='button']"
                )
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(3)
                page_num += 1
            except NoSuchElementException:
                print(f"\n✅ No Next button - reached end")
                break
        
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    return results


# ==================== STEP 6: EXTRACT & CLEAN DATA ====================

def extract_details_from_page(driver):
    """
    Extract all 12 fields from currently loaded detail page.
    Uses div IDs for reliable extraction.
    """
    try:
        # Wait for content
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'makeTableRow_Content')]"))
        )
        time.sleep(1)
        
        # Click Expand All
        try:
            expand_buttons = driver.find_elements(By.XPATH, "//img[contains(@src, 'HeadArrowDown.png')]")
            if expand_buttons:
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                time.sleep(2)
        except:
            pass
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        def get_div_content(div_id):
            """Get content from div by ID"""
            div = soup.find("div", {"id": div_id})
            if div:
                return div.get_text(strip=True)
            return ""
        
        # Extract DA number from page
        da_number = ""
        try:
            match = re.search(r'(PCD\d+/\d+|RA\d+/\d+|RS\d+/\d+|DA\d+/\d+|MA\d+/\d+)', driver.page_source)
            if match:
                da_number = match.group(1)
        except:
            pass
        
        # Extract from div IDs
        details_text = get_div_content("lblDetails")
        decision_text = get_div_content("lblDecision")
        categories_text = get_div_content("lblCat")
        properties_text = get_div_content("lblProp")
        people_text = get_div_content("lblPeople")
        progress_text = get_div_content("lblProg")
        fees_text = get_div_content("lblFees")
        documents_text = get_div_content("lblDocs")
        contact_text = get_div_content("lbl91")
        
        # Parse Details for Description and Submitted Date
        description = ""
        submitted_date = ""
        if details_text:
            if "Description:" in details_text:
                parts = details_text.split("Submitted:")
                description = parts[0].replace("Description:", "").strip()
                if len(parts) > 1:
                    submitted_date = parts[1].strip()
            else:
                description = details_text
        
        # Parse Properties for address
        property_address = ""
        if properties_text:
            property_address = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', properties_text).strip()
        
        # Parse People for applicant
        applicant = ""
        if people_text:
            applicant = people_text.replace("Applicant:", "").strip()
        
        # Build record
        record = {
            "DA_Number": da_number,
            "Detail_URL": driver.current_url,
            "Description": description,
            "Submitted_Date": submitted_date,
            "Decision": decision_text,
            "Categories": categories_text,
            "Property_Address": property_address,
            "Applicant": applicant,
            "Progress": progress_text,
            "Fees": fees_text,
            "Documents": documents_text,
            "Contact_Council": contact_text,
        }
        
        # ========== STEP 6: APPLY EXACT CLEANING RULES ==========
        
        # Rule 1: Fees cleaning - EXACT TEXT MATCH
        if record["Fees"].strip() == FEES_NO_FEES_TEXT:
            record["Fees"] = "Not required"
        
        # Rule 2: Contact_Council cleaning - EXACT TEXT MATCH
        if record["Contact_Council"].strip() == CONTACT_NO_EXHIBITION_TEXT:
            record["Contact_Council"] = "Not required"
        
        return record
        
    except Exception as e:
        return None


def scrape_all_records(driver, da_url_list):
    """
    Scrape all records sequentially from collected DA+URL list.
    Ensures no duplicates.
    """
    records = []
    seen_das = set()
    
    print("\n" + "="*70)
    print("STEP 6: Scraping All Records Sequentially")
    print("="*70)
    print(f"Total records to scrape: {len(da_url_list)}\n")
    
    for i, item in enumerate(da_url_list, 1):
        da = item["da"]
        url = item["url"]
        
        print(f"[{i:3d}/{len(da_url_list)}] DA: {da:<15}", end=" ")
        
        # Skip if already scraped (duplicate prevention)
        if da in seen_das:
            print("⚠️  (duplicate, skipped)")
            continue
        
        try:
            # Navigate to detail page
            driver.get(url)
            
            # Extract data
            record = extract_details_from_page(driver)
            
            if record:
                # Fill in DA if missing
                if not record.get("DA_Number"):
                    record["DA_Number"] = da
                
                # Fill in URL if missing
                if not record.get("Detail_URL"):
                    record["Detail_URL"] = url
                
                records.append(record)
                seen_das.add(da)
                print("✅")
            else:
                print("⚠️  (no data)")
        
        except Exception as e:
            print(f"❌ ({type(e).__name__})")
            continue
    
    print(f"\n{'='*70}")
    print(f"✅ Scraping Complete")
    print(f"   Total records extracted: {len(records)}")
    print(f"   Duplicates prevented: {len(da_url_list) - len(records)}")
    print(f"{'='*70}\n")
    
    return records


# ==================== STEP 7: SAVE TO CSV ====================

def save_records_to_csv(records, filename):
    """STEP 7: Save all records to CSV with exact 12 headers."""
    print("\n" + "="*70)
    print("STEP 7: Save to CSV")
    print("="*70)
    
    try:
        df = pd.DataFrame(records)
        
        # Ensure all headers exist
        for header in HEADERS:
            if header not in df.columns:
                df[header] = ""
        
        # Reorder columns to match exact header order
        df = df[HEADERS]
        
        # Save to CSV
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        
        print(f"\n✅ CSV SAVED SUCCESSFULLY")
        print(f"   File: {filename}")
        print(f"   Total Records: {len(df)}")
        print(f"   Columns: {len(HEADERS)}")
        print(f"\n   Column Headers:")
        for i, header in enumerate(HEADERS, 1):
            print(f"     {i:2d}. {header}")
        
        if len(df) > 0:
            print(f"\n   Data Quality:")
            print(f"     Non-empty DA_Numbers: {(df['DA_Number'] != '').sum()}/{len(df)}")
            print(f"     Records with Description: {(df['Description'] != '').sum()}/{len(df)}")
            print(f"     Records with Decision: {(df['Decision'] != '').sum()}/{len(df)}")
            print(f"     Fees (cleaned): {(df['Fees'] != '').sum()}/{len(df)}")
            print(f"     Contact_Council (cleaned): {(df['Contact_Council'] != '').sum()}/{len(df)}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== MAIN EXECUTION ====================

def main():
    """Main execution - All 7 Steps."""
    driver = create_driver(headless=False)
    
    try:
        print("\n" + "="*70)
        print("🚀 SHOALHAVEN DA TRACKING SCRAPER - FINAL COMPLETE")
        print("="*70)
        print(f"📅 Date Range: {START_DATE} to {END_DATE}")
        print(f"📂 Output File: {OUTPUT_CSV}")
        print(f"✨ Features:")
        print(f"   • URL normalization (relative → absolute)")
        print(f"   • Sequential scraping (no duplicates)")
        print(f"   • Exact cleaning rules applied")
        print(f"   • 12-column CSV output")
        print("="*70 + "\n")
        
        # STEPS 1-4: Setup and Search
        if not step_1_accept_disclaimer(driver):
            return
        if not step_2_navigate_da_tracking(driver):
            return
        if not step_3_open_advanced_search(driver):
            return
        if not step_4_set_date_range(driver, START_DATE, END_DATE):
            return
        if not step_4b_click_search(driver):
            return
        
        # Check for results
        if "No records" in driver.page_source:
            print("❌ No records found")
            return
        
        # Extract total pages
        total_items, total_pages = extract_total_pages_and_items(driver)
        
        if total_pages is None:
            print("❌ Could not extract total pages")
            return
        
        print(f"\n📊 Search Results Detected:")
        print(f"   Total Items: {total_items}")
        print(f"   Total Pages: {total_pages}\n")
        
        # STEP 5: Collect DA + URLs
        da_url_list = collect_da_and_urls(driver, total_pages)
        
        if not da_url_list:
            print("❌ No DA+URL pairs collected")
            return
        
        # STEP 6: Scrape all records
        all_records = scrape_all_records(driver, da_url_list)
        
        if not all_records:
            print("❌ No records extracted")
            return
        
        # STEP 7: Save to CSV
        save_records_to_csv(all_records, OUTPUT_CSV)
        
        # Summary
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETE - SUCCESS")
        print("="*70)
        print(f"   Expected Records: {total_items}")
        print(f"   Actual Records: {len(all_records)}")
        print(f"   Success Rate: {(len(all_records)/total_items)*100:.1f}%")
        print(f"   DA+URLs Collected: {len(da_url_list)}")
        print(f"   Pages Processed: {total_pages}")
        print(f"   Duplicates Prevented: ✅")
        print(f"   Data Cleaning: Applied ✅")
        print(f"   CSV Format: 12 exact headers ✅")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        driver.quit()
        print("✅ WebDriver closed\n")


if __name__ == "__main__":
    main()
