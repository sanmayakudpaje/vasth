import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
print(f"Supabase URL: {url}")
print(f"Supabase Key: {'***' if key else 'Not Set'}")

supabase: Client = create_client(url, key)

@app.route('/')
def index():
    # Fetch data from a table
    response = supabase.table("orders").select("*").execute()
    orders = response.data
    return render_template('index.html', orders=orders)

@app.route('/reserve', methods=['POST'])
def reserve():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    guests = data.get('guests')
    dining_experience = (data.get('dining_experience') or '').strip()
    location = (data.get('location') or '').strip()

    if not name or not dining_experience or not location or not isinstance(guests, int) or guests < 1:
        return jsonify({'error': 'Invalid reservation data'}), 400

    try:
        response = supabase.table('orders').insert({
            'name': name,
            'guests': guests,
            'dining_experience': dining_experience,
            'location': location
        }).execute()

        if hasattr(response, 'error') and response.error:
            print(f"Supabase error: {response.error}")
            return jsonify({'error': str(response.error)}), 500

        return jsonify({'success': True, 'order': response.data}), 201
    except Exception as e:
        print(f"Exception during insert: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)