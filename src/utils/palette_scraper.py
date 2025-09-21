"""
colour palette scraper for getting trendy colour palettes from Coolors.co
this gives us a database of popular colour combos to match against
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


def load_saved_palettes(palettes_file):
    """load what we've already scraped so we don't duplicate and keep creating a growing database"""
    if os.path.exists(palettes_file):
        with open(palettes_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_palettes(palettes, palettes_file):
    """write our palette collection to file"""
    with open(palettes_file, "w", encoding="utf-8") as f:
        json.dump(palettes, f, ensure_ascii=False, indent=2)


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
    """get the trending colour palettes from Coolors.co"""
    driver = get_driver()
    
    try:
        print("Loading Coolors.co trending page...")
        driver.get("https://coolors.co/palettes/trending")
        time.sleep(3)

        # scroll down to load more palettes
        print("Scrolling to load more palettes...")
        for _ in tqdm(range(5), desc="Loading palettes"):
            driver.execute_script("window.scrollBy(0, 1000)")
            time.sleep(1)

        # use JavaScript to grab all the data at once - much faster
        js_script = """
        const palettes = {};
        const cards = document.querySelectorAll('.palette-card');
        
        cards.forEach((card, index) => {
            // get the palette name
            const nameEl = card.querySelector('.palette-card_name');
            const name = nameEl ? nameEl.textContent.trim() : `Palette ${index+1}`;
            
            // grab all the hex colours
            const colorDivs = card.querySelectorAll('.palette-card_colors div');
            const colours = [];
            
            colorDivs.forEach(div => {
                const span = div.querySelector('span');
                if(span){
                    const hexText = span.textContent.trim();
                    if(hexText.length === 6){
                        colours.push('#' + hexText.toUpperCase());
                    }
                }
            });
            
            if(colours.length > 0) {
                palettes[name] = colours;
            }
        });
        
        return palettes;
        """
        
        palette_data = driver.execute_script(js_script)
        
        # only keep the ones we asked for
        limited_palettes = dict(list(palette_data.items())[:max_palettes])
        print(f"Scraped {len(limited_palettes)} colour palettes")
        
        return limited_palettes
        
    finally:
        driver.quit()


def update_palette_database(palettes_file, max_palettes=50):
    """add new palettes to our collection without duplicating"""
    
    # load what we already have
    saved = load_saved_palettes(palettes_file)
    print(f"Found {len(saved)} existing palettes")

    # scrape the latest trending ones
    new_scrape = scrape_trending_palettes(max_palettes=max_palettes)
    print(f"Scraped {len(new_scrape)} palettes from Coolors")

    # only add the new ones
    added = 0
    for name, colours in new_scrape.items():
        if name not in saved:
            saved[name] = colours
            added += 1

    # save everything back
    save_palettes(saved, palettes_file)
    print(f"Added {added} new palettes. Total collection: {len(saved)}")

    return saved