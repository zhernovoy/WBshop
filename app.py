from flask import Flask, render_template, request
from wb_scraper import get_items_from_wildberries
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    items = []
    url = ""
    error = None
    
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if url:
            try:
                items = get_items_from_wildberries(url)
                if not items:
                    error = "No items found for the given URL"
            except Exception as e:
                error = f"Error occurred: {str(e)}"
    
    return render_template('index.html', items=items, url=url, error=error)

if __name__ == '__main__':
    app.run(debug=True) 