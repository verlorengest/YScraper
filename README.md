
# YScraper

![app_icon](https://github.com/user-attachments/assets/55216568-212b-4183-ac74-ac3665176902)


YScraper is a powerful GUI-based YouTube comment scraper built with Python and Selenium. It allows users to extract comments, replies, and profile photos from individual videos, channels, or bulk lists—without relying on YouTube’s official API.


---

## 🔧 Features

* **Multiple Scraping Modes**: Scrape from a single video, full channel (with optional video limits), or list of URLs.
* **Replies & Profile Photos**: Optionally include replies and profile pictures for enriched data.
* **GUI Interface**: Built with Tkinter, featuring tabs for scraping, viewing, filtering, and exporting data.
* **Data Export**: Save comments in JSON, CSV, or XML formats.
* **Smart Reply Expansion**: Interacts with the YouTube interface to fully expand hidden replies.
* **Pretty View & Filtering**: Tree view for navigating comments/replies and filtering by author or content.
* **Headless or Visible Mode**: Choose between headless execution or debug-visible Chrome browser.
* **No API Keys Needed**: Works without relying on YouTube Data API, bypasses cookie banners using Selenium.

---

## 🚀 How to Launch

### Prerequisites

* Python 3.7+
* Chrome installed
* Recommended: Use a virtual environment

Double click to launch.bat and you are good to go.

Or,

### Install Dependencies

```bash
pip install -r requirements.txt
```

> If `requirements.txt` is not available, manually install:

```bash
pip install selenium undetected-chromedriver requests textblob
```

### Run the Application

```bash
python YScraper.py
```

This will launch a GUI window where you can choose scrape mode and options.

---

## 📦 Output Formats

* **JSON**: Structured for all fields, including replies.
* **CSV**: Flat structure suitable for Excel or data processing.
* **XML**: For hierarchical data or integration with XML pipelines.



## 🧠 Notes

* This tool uses `undetected-chromedriver` to avoid bot detection.
* You can enable “Debug Mode” to watch the scraping process live in a browser.
* For large scraping jobs (like full channels), results may take a while due to scroll-based comment loading.

---

## Support
If you are benefiting from this project, consider supporting it
https://kaansoyler.gumroad.com/l/YScraper

