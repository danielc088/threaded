"""
colour palette scraper for getting trendy colour palettes from coolors.co
this gives us a database of popular colour combos to match against
helps us understand what colours actually look good together
"""

import time, re, sys, os, json
from bs4 import BeautifulSoup
from tqdm import tqdm
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_driver():
    """set up chrome to scrape"""
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument("--headless=new")  # run in background
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1200")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--log-level=3")  # shut up chrome
    
    # hide selenium errors too
    sys.stderr = open(os.devnull, "w")
    return webdriver.Chrome(options=options)


def scrape_trending_palettes(max_palettes=50):
    """get the trending colour palettes from coolors.co"""
    driver = get_driver()
    
    try:
        print("loading coolors.co trending page...")
        driver.get("https://coolors.co/palettes/trending")
        time.sleep(3)

        # scroll down to load more palettes
        print("scrolling to load more palettes...")
        for _ in tqdm(range(5), desc="loading palettes"):
            driver.execute_script("window.scrollBy(0, 1000)")
            time.sleep(1)

        # use javascript to grab all the data at once - much faster
        js_script = """
        const palettes = {};
        const cards = document.querySelectorAll('.palette-card');
        
        cards.forEach((card, index) => {
            // get the palette name
            const nameEl = card.querySelector('.palette-card_name');
            const name = nameEl ? nameEl.textContent.trim() : `palette ${index+1}`;
            
            // grab all the hex colours
            const colorDivs = card.querySelectorAll('.palette-card_colors div');
            const colors = [];
            
            colorDivs.forEach(div => {
                const span = div.querySelector('span');
                if(span){
                    const hexText = span.textContent.trim();
                    if(hexText.length === 6){
                        colors.push('#' + hexText.toUpperCase());
                    }
                }
            });
            
            if(colors.length > 0) {
                palettes[name] = colors;
            }
        });
        
        return palettes;
        """
        
        palette_data = driver.execute_script(js_script)
        
        # only keep the ones we asked for
        limited_palettes = dict(list(palette_data.items())[:max_palettes])
        print(f"scraped {len(limited_palettes)} colour palettes")
        
        return limited_palettes
        
    finally:
        driver.quit()


def update_palette_database(db, max_palettes=50):
    """add new palettes to database without duplicating"""
    
    # get existing palettes from database
    existing_palettes = db.get_color_palettes()
    existing_names = {p['name'] for p in existing_palettes}
    print(f"found {len(existing_palettes)} existing palettes in database")

    # scrape the latest trending ones
    new_scrape = scrape_trending_palettes(max_palettes=max_palettes)
    print(f"scraped {len(new_scrape)} palettes from coolors")

    # only add the new ones
    added = 0
    for name, colors in new_scrape.items():
        if name not in existing_names:
            db.add_color_palette(name, colors, source="coolors_trending")
            added += 1

    print(f"added {added} new palettes to database")
    total_count = len(existing_palettes) + added
    print(f"total collection: {total_count} palettes")

    return added


if __name__ == "__main__":
    # for testing
    from data.database.models import WardrobeDB
    db = WardrobeDB()
    update_palette_database(db, max_palettes=100)