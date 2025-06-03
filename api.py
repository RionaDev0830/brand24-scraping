from flask import Flask, jsonify
from brand24_scraper import Brand24Scraper

app = Flask(__name__)

@app.route("/scrape", methods=["GET"])
def scrape():
    scraper = Brand24Scraper()
    try:
        if scraper.login():
            if scraper.scrape_data():
                with open("scraped_data.json", "r", encoding="utf-8") as f:
                    data = f.read()
                return jsonify({"status": "success", "data": data})
            else:
                return jsonify({"status": "fail", "message": "Scraping failed"}), 500
        else:
            return jsonify({"status": "fail", "message": "Login failed"}), 401
    finally:
        scraper.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
