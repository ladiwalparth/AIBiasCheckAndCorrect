import requests
from bs4 import BeautifulSoup, Comment
from typing import Optional
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setting up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('parse.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


class WebParser:

    def __init__(self, max_content_length: int, chunk_size: int, use_selenium: bool = False):
        self.max_content_length = max_content_length
        self.chunk_size = chunk_size
        self.use_selenium = use_selenium

    @staticmethod
    def _tag_visible(element):
        if element.strip() == '':
            return False
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', 'svg', 'path', 'noscript', 'header', 'footer', 'nav', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        if element.parent.get('hidden'):
            return False
        if element.parent.get('aria-hidden') == 'true':
            return False

        return True

    @staticmethod
    def _text_from_html(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        texts = soup.find_all(text=True)
        visible_texts = filter(WebParser._tag_visible, texts)

        return ' '.join(t.strip() for t in visible_texts)

    def _get_html_using_selenium(self, uri: str) -> str:
        """ Use Selenium to get the full page source (JS rendered content). """
        options = Options()
        options.headless = True  # Run the browser in headless mode (without opening a window)

        # Initialize the WebDriver (Chrome)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            driver.get(uri)
            time.sleep(3)  # Allow time for JavaScript to load the page content
            html_content = driver.page_source  # Get the page source after JS renders it
        except Exception as e:
            logger.error(f"Error with Selenium: {e}")
            html_content = ""
        finally:
            driver.quit()

        return html_content

    def parse(self, uri: str) -> Optional[str]:
        try:
            if self.use_selenium:
                # Try using Selenium to get the content (for dynamically loaded content)
                logger.info(f"Using Selenium to scrape {uri}")
                html_content = self._get_html_using_selenium(uri)

                if not html_content:
                    logger.warning(f"Failed to fetch content using Selenium for {uri}")
                    return None
            else:
                # Fall back to requests for static content
                logger.info(f"Using requests to scrape {uri}")
                with requests.get(uri, stream=True) as response:
                    response.raise_for_status()

                    content = []
                    content_length = 0

                    for chunk in response.iter_content(chunk_size=self.chunk_size, decode_unicode=True):
                        content.append(chunk)
                        content_length += len(chunk)

                        if content_length > self.max_content_length:
                            logger.warning('Max content length %d exceeded for URI %s, truncating', self.max_content_length, uri)
                            break

                    html_content = ''.join(content)

            # Return the visible text from the fetched HTML content
            return self._text_from_html(html_content)

        except requests.RequestException as e:
            logger.error(f"Error parsing URI {uri}: {e}")
            return None
