# Redfin Median Price API

A FastAPI application that fetches and stores 3-year median sale prices for cities across the United States using data from Redfin.

## Overview

This application provides a simple API endpoint to retrieve median home sale prices for any US city. It scrapes data from Redfin's housing market pages, stores it in MongoDB for improved performance on subsequent requests, and serves it through a clean REST API.

## Features

- **Real-time Data Scraping**: Fetches the latest median price data from Redfin on demand
- **MongoDB Caching**: Stores retrieved data to minimize scraping operations and improve response times
- **Dockerized Environment**: Runs in containers for easy deployment and consistent environment
- **Robust Error Handling**: Gracefully handles network errors and missing data
- **IP Blocking Prevention**: Uses rotating user agents and request delays

The application consists of the following components:

1. **FastAPI Backend**: Handles API requests and serves cached or freshly scraped data
2. **Web Scraper Module**: Extracts median price data from Redfin's housing market pages
3. **MongoDB Database**: Stores cached results with timestamps for efficient retrieval
4. **Docker Containers**: Packages all components for easy deployment

## API Endpoints

### Get Median Sale Prices

```
GET /median-prices?state={state_code}&city={city_name}
```

**Parameters:**
- `state`: State abbreviation (e.g., "TX", "CA", "NY")
- `city`: City name (e.g., "Austin", "San Francisco", "New York")

**Response Example:**
```json
{
   "2022-05": 640000,
   "2022-06": 635000,
   "2022-07": 625000,
   "2022-08": 610000,
   ...
   "2025-04": 585000,
   "2025-05": 590000

}
```

## Installation and Setup

### Prerequisites

- Python 3.11
- Docker and Docker Compose
- Git

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/ahmadbinshafqat/redfin-median-api.git
   cd redfin-median-api
   ```

2. Start the containers:
   ```bash
   docker-compose up --build
   ```

3. The API will be available at `http://localhost:8000`

4. Access the API documentation at `http://localhost:8000/docs`


## Usage Examples (Locally)

### Using curl

```bash
# Get median prices for Austin, TX
curl "http://localhost:8000/median-prices?state=TX&city=Austin"

# Get median prices for San Francisco, CA
curl "http://localhost:8000/median-prices?state=CA&city=San%20Francisco"
```

### Run Manually (Without Docker)

1. Clone the repository:
   ```bash
   git clone https://github.com/ahmadbinshafqat/redfin-median--api.git
   cd redfin-median-api
   ```

2. Create and activate a virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

4. Run the FastAPI server:
```bash
uvicorn app.main:app --reload
```
5. The API will be available at:
http://localhost:8000

6. Access the interactive API documentation at:
http://localhost:8000/docs

## 🧪 Tests

### Prerequisites

 **Python 3.11** is required.  
  Make sure you're using Python 3.11:

  ```bash
  python --version
  ```

1. Install requirements:
```bash
pip install -r requirements.txt
```
2. Run tests:
```bash
pytest tests
```
3. Run tests with coverage:
```bash
coverage run -m pytest tests
```
4. Generate a coverage report:
```bash
coverage report
```
> ✅ **Note**: Test coverage is **95%+**, ensuring the application's core functionality is well tested.


## Technical Details

### Scraping Approach

1. We use Redfin's autocomplete API to get the correct city code
2. The scraper extracts median price data points from the housing market chart
3. Data is processed and stored in a normalized format

### Rate Limiting and IP Protection

- Random delays between requests (1-3 seconds by default)
- Rotating user agents to mimic different browsers

### Data Storage

- MongoDB is used for efficient document storage
- Each city's data is stored as a separate document
- A timestamp field tracks when data was last updated


## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Redfin](https://www.redfin.com/) for providing the housing market data
- [MongoDB](https://www.mongodb.com/) for the database solution