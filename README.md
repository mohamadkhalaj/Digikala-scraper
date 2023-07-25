# DigiKala Scraper

This is a Python script that scrapes product data from the [Digikala](https://www.digikala.com/) website. The script uses asyncio and aiohttp to efficiently make HTTP requests and parse the JSON responses.
The script fetches the product data from a specified category URL, sorts the products based on buyer suggestions, and saves the sorted data to a JSON file.
## Usage

To run the script, you'll need Python 3.7 or later installed on your system. You can install the required dependencies by running:

```
pip install aiohttp==3.8.4
```

To start the scraper, run the following command:

```
python digikala_scraper.py [category_url]
```

Replace `[category_url]` with the URL of the category you want to scrape. For example:

```
python digikala_scraper.py https://www.digikala.com/search/category-cell-phone-data-cable/?attributes%5B2204%5D%5B0%5D=16958&types%5B0%5D=4804
```

The script will fetch data from the specified category and save the scraped data to a JSON file in the current directory.

## Configuration

You can modify the following constants in the `DigiKalaScraper` class to configure the behavior of the scraper:

- `MAX_CONCURRENT_REQUESTS`: The maximum number of concurrent HTTP requests to make.
- `MAX_RETRIES`: The maximum number of times to retry a failed HTTP request.
- `TIMEOUT`: The timeout for each HTTP request, in seconds.

## Output

The script saves the scraped data to a JSON file with a unique filename based on the category name. The file contains an array of product objects, each with the following fields:

- `url`: The URL of the product.
- `count`: Number of total likes to this product.
- `percentage`: Percentage of how users are satisfied about this product.
