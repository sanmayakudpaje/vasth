import os
from flask import Flask, render_template, request, jsonify
from supabase import SupabaseException, create_client, Client
from dotenv import load_dotenv
from typing import Optional, Tuple

load_dotenv()  # Load environment variables from .env file

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

def _clean_env(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    # Vercel/UI env values are sometimes pasted with wrapping quotes.
    if (cleaned.startswith("'") and cleaned.endswith("'")) or (
        cleaned.startswith('"') and cleaned.endswith('"')
    ):
        cleaned = cleaned[1:-1].strip()
    return cleaned or None


def _resolve_supabase_key() -> Tuple[Optional[str], Optional[str]]:
    # Ordered by preferred privilege level and common naming.
    key_candidates = [
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_KEY",
        "SUPABASE_ANON_KEY",
        "SUPABASE_PUBLISHABLE_KEY",
    ]
    for key_name in key_candidates:
        key_value = _clean_env(os.getenv(key_name))
        if key_value:
            return key_name, key_value
    return None, None


# Initialize Supabase client
url = _clean_env(os.getenv("SUPABASE_URL"))
key_name, key = _resolve_supabase_key()
print(f"Supabase URL set: {'yes' if url else 'no'}")
print(f"Supabase key source: {key_name or 'none'}")

if not url or not key:
    raise RuntimeError(
        "Supabase credentials are missing. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
        "or SUPABASE_KEY (or SUPABASE_ANON_KEY) in Vercel environment variables."
    )

try:
    supabase: Client = create_client(url, key)
except SupabaseException as e:
    if "Invalid API key" in str(e) and not key.startswith("eyJ"):
        raise RuntimeError(
            "Supabase Python client rejected this key format. Use the legacy anon or service_role JWT "
            "(starts with eyJ...) from Project Settings → API, or upgrade supabase package (see requirements.txt). "
            f"Current key env: {key_name}."
        ) from e
    raise

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