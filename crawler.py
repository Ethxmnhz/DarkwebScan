import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
import tkinter as tk
from tkinter import messagebox, scrolledtext

# Set of visited URLs to prevent revisiting the same page
visited_links = set()

# Maximum retries and request timeout in seconds
MAX_RETRIES = 3
TIMEOUT = 60

# Add a user-agent to mimic normal browser requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def log_message(message, text_area):
    """Logs messages in the text area."""
    text_area.insert(tk.END, message + "\n")
    text_area.see(tk.END)

def analyze_page(soup, url, text_area):
    """Analyze and log details of the page."""
    log_message(f"Title: {soup.title.string if soup.title else 'No title found'}", text_area)

    # Collect all links on the page first
    links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(url, href)
        links.add(full_url)

    # Log the found links
    log_message(f"Found {len(links)} links on {url}: {links}", text_area)

    # Proceed with the rest of the analysis
    log_message(f"Found {len(soup.find_all('meta'))} meta tags", text_area)
    log_message(f"Found {len(soup.find_all('img'))} images", text_area)
    log_message(f"Found {len(soup.find_all('script'))} scripts", text_area)
    log_message(f"Found {len(soup.find_all('form'))} forms", text_area)

    # Check for certain keywords
    keywords = ["bitcoin", "security", "privacy", "exploit"]
    for keyword in keywords:
        if keyword in soup.text.lower():
            log_message(f"Keyword '{keyword}' found on {url}", text_area)

def get_page_with_retries(session, url, text_area):
    """Handle requests with retries in case of failures."""
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            log_message(f"Attempt {attempt + 1} failed: {e}", text_area)
            if attempt + 1 < MAX_RETRIES:
                log_message("Retrying...", text_area)
                time.sleep(5)
            else:
                log_message(f"Failed to connect to {url} after {MAX_RETRIES} attempts.", text_area)
                return None

def crawl_with_selenium(url, text_area):
    """Crawl the page using Selenium for dynamic content."""
    tor_browser_path = "C:/Users/minhaz/OneDrive/Desktop/Tor Browser/Browser/firefox.exe"
    geckodriver_path = "C:/Users/minhaz/Downloads/geckodriver.exe"

    options = webdriver.FirefoxOptions()
    options.binary_location = tor_browser_path
    service = Service(geckodriver_path)

    driver = webdriver.Firefox(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(5)  # Wait for the page to load
        soup = BeautifulSoup(driver.page_source, 'lxml')
        analyze_page(soup, url, text_area)

        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            links.add(full_url)

        return links
    finally:
        driver.quit()

def crawl_onion_site(url, depth, use_selenium, text_area):
    """Crawl a given .onion URL to a specified depth."""
    if depth < 0 or url in visited_links:
        return

    visited_links.add(url)
    log_message(f"Connecting to {url}...", text_area)

    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://localhost:9150', 
        'https': 'socks5h://localhost:9150'
    }

    if use_selenium:
        log_message("Using Selenium for dynamic content.", text_area)
        links = crawl_with_selenium(url, text_area)
    else:
        response = get_page_with_retries(session, url, text_area)
        if response is None:
            return

        soup = BeautifulSoup(response.text, 'lxml')
        analyze_page(soup, url, text_area)

        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            links.add(full_url)

    log_message(f"Found {len(links)} links on {url}.", text_area)
    for link in links:
        if link not in visited_links and link.startswith(url):
            log_message(f"Proceeding to crawl link: {link}", text_area)
            crawl_onion_site(link, depth - 1, use_selenium, text_area)

def start_crawling():
    onion_url = url_entry.get()
    use_selenium = selenium_var.get()

    if onion_url.startswith("http://") and onion_url.endswith(".onion"):
        log_message("Starting crawl...", log_area)
        crawl_onion_site(onion_url, depth=3, use_selenium=use_selenium, text_area=log_area)
    else:
        messagebox.showerror("Invalid URL", "Please enter a valid .onion URL.")

# GUI setup
root = tk.Tk()
root.title("Onion Crawler")

frame = tk.Frame(root)
frame.pack(pady=10)

url_label = tk.Label(frame, text="Enter .onion URL:")
url_label.grid(row=0, column=0, padx=5, pady=5)
url_entry = tk.Entry(frame, width=50)
url_entry.grid(row=0, column=1, padx=5, pady=5)

selenium_var = tk.BooleanVar()
selenium_checkbox = tk.Checkbutton(frame, text="Use Selenium", variable=selenium_var)
selenium_checkbox.grid(row=1, column=0, columnspan=2, pady=5)

crawl_button = tk.Button(frame, text="Start Crawl", command=start_crawling)
crawl_button.grid(row=2, column=0, columnspan=2, pady=10)

log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
log_area.pack(pady=10)

root.mainloop()
