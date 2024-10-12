from flask import Flask, render_template, request, jsonify, Response
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import time
import threading
import queue
import json

app = Flask(__name__)

# Global Variables
visited_links = set()
live_logs = queue.Queue()
stats = {'pages_visited': 0, 'links_found': 0}
sitemap_structure = {}

# Crawl settings
MAX_RETRIES = 3
TIMEOUT = 60
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def get_page_with_retries(session, url):
    """Handles requests with retries in case of failures."""
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            log_message(f"Attempt {attempt + 1} failed: {e}", url)
            if attempt + 1 < MAX_RETRIES:
                log_message("Retrying...", url)
                time.sleep(2)
            else:
                log_message(f"Failed to connect to {url} after {MAX_RETRIES} attempts.", url)
                return None

def analyze_page(soup, url):
    """Analyzes a page for links and logs information."""
    log_message(f"Analyzing page: {url}")
    
    links = set()
    for link in soup.find_all('a', href=True):
        full_url = urljoin(url, link['href'])
        if is_valid_url(full_url, url):
            links.add(full_url)

    log_message(f"Found {len(links)} links on {url}", url)
    
    if len(links) == 0:
        live_logs.put(json.dumps({'no_links': True, 'url': url}))

    # Update statistics
    stats['pages_visited'] += 1
    stats['links_found'] += len(links)

    return links

def log_message(message, url=None):
    """Logs a message to be sent to the front-end."""
    live_logs.put(json.dumps({'log': message, 'url': url}))

def crawl_site(url, depth):
    """Recursively crawls a website up to a given depth."""
    if depth < 0 or url in visited_links:
        return

    visited_links.add(url)
    log_message(f"Starting crawl for {url}", url)

    session = requests.Session()
    session.proxies = {
        'http': 'socks5h://localhost:9150', 
        'https': 'socks5h://localhost:9150'
    }

    response = get_page_with_retries(session, url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    links = analyze_page(soup, url)

    # Update the sitemap structure
    parent_id = urlparse(url).netloc + urlparse(url).path
    if parent_id not in sitemap_structure:
        sitemap_structure[parent_id] = []

    for link in links:
        sitemap_structure[parent_id].append(link)
        live_logs.put(json.dumps({'url': link, 'parent_id': parent_id}))

    for link in links:
        crawl_site(link, depth - 1)

def is_valid_url(url, base_url):
    """Ensures the URL is in scope (same domain)."""
    return urlparse(url).netloc == urlparse(base_url).netloc

def start_crawl_thread(url, depth):
    """Starts the crawling process in a separate thread."""
    thread = threading.Thread(target=crawl_site, args=(url, depth))
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_crawl')
def start_crawl():
    url = request.args.get('url')
    depth = int(request.args.get('depth', 3))
    reset_crawl_state()
    start_crawl_thread(url, depth)
    return Response(stream_with_logs(), content_type='text/event-stream')

def stream_with_logs():
    """Stream live logs and sitemap updates."""
    while True:
        if not live_logs.empty():
            log = live_logs.get()
            yield f"data: {log}\n\n"
        time.sleep(1)

def reset_crawl_state():
    """Resets the crawl state before starting a new crawl."""
    global visited_links, stats, sitemap_structure
    visited_links.clear()
    stats = {'pages_visited': 0, 'links_found': 0}
    sitemap_structure.clear()

@app.route('/stats')
def get_stats():
    return jsonify(stats)

if __name__ == "__main__":
    app.run(debug=True)
