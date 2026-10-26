"""
=============================================================================
MADADGAR (مددگار) — Karachi Emergency Ambulance Dispatch System
Backend & Frontend: 100% Python Flask with Pure HTML, CSS & JavaScript
=============================================================================
"""

import math
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, send_from_directory
from flask_cors import CORS

# Optional imports for PostgreSQL and Gemini AI
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DIST_DIR = os.path.join(BASE_DIR, 'dist')

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = "madadgar_karachi_emergency_super_secret_key"
CORS(app)

# =============================================================================
# 1. DATABASE CONFIGURATION (PostgreSQL + Local Fallback)
# =============================================================================
# PostgreSQL configuration matching user's local pgAdmin setup
PG_CONFIG = {
    "dbname": os.environ.get("PGDATABASE", "emergency_db"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", ""),
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432")
}

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "emergency_db.sqlite")

def get_db_connection():
    """
    Connects to PostgreSQL if available on user's machine (via pgAdmin).
    If PostgreSQL is unreachable (e.g. in cloud container), falls back
    to SQLite with the exact same tables and columns.
    """
    if PSYCOPG2_AVAILABLE:
        try:
            conn = psycopg2.connect(**PG_CONFIG)
            return conn, "postgres"
        except Exception:
            pass

    # SQLite fallback
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"

def init_db():
    """Initializes tables and seeds initial fleet and staff accounts."""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgres":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.drivers (
                vehicle_number character varying(50) NOT NULL PRIMARY KEY,
                name character varying(100) NOT NULL,
                contact character varying(20) NOT NULL,
                current_lat double precision NOT NULL,
                current_lng double precision NOT NULL,
                is_available boolean DEFAULT true,
                organization character varying(50) DEFAULT 'Edhi',
                area_name character varying(150)
            );

            CREATE TABLE IF NOT EXISTS public.emergency_requests (
                request_id SERIAL PRIMARY KEY,
                user_name character varying(100) NOT NULL,
                user_contact character varying(20) NOT NULL,
                patient_lat double precision NOT NULL,
                patient_lng double precision NOT NULL,
                assigned_vehicle character varying(50),
                status character varying(20) DEFAULT 'Pending',
                emergency_type character varying(100) DEFAULT 'General Emergency',
                patient_address text,
                distance_km double precision DEFAULT 0.0,
                eta_minutes integer DEFAULT 5,
                created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS public.users (
                user_id SERIAL PRIMARY KEY,
                username character varying(50) NOT NULL UNIQUE,
                password character varying(50) NOT NULL,
                role character varying(20) NOT NULL,
                vehicle_number character varying(50)
            );

            -- Ensure columns exist
            ALTER TABLE public.emergency_requests ADD COLUMN IF NOT EXISTS emergency_type character varying(100) DEFAULT 'General Emergency';
            ALTER TABLE public.emergency_requests ADD COLUMN IF NOT EXISTS patient_address text;
            ALTER TABLE public.emergency_requests ADD COLUMN IF NOT EXISTS distance_km double precision DEFAULT 0.0;
            ALTER TABLE public.emergency_requests ADD COLUMN IF NOT EXISTS eta_minutes integer DEFAULT 5;
            ALTER TABLE public.drivers ADD COLUMN IF NOT EXISTS organization character varying(50) DEFAULT 'Edhi';
            ALTER TABLE public.drivers ADD COLUMN IF NOT EXISTS area_name character varying(150);
        """)

        # Seed drivers if empty
        cursor.execute("SELECT COUNT(*) FROM public.drivers;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO public.drivers (vehicle_number, name, contact, current_lat, current_lng, is_available, organization, area_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (vehicle_number) DO NOTHING;
            """, [
                ('EDHI-101', 'Tariq Mehmood', '0300-1122331', 24.8615, 67.0315, True, 'Edhi', 'Saddar Sector, Karachi'),
                ('CHHIPA-201', 'Mohammad Farooq', '0312-9988772', 24.8738, 67.0601, True, 'Chhipa', 'PECHS / Nursery Station'),
                ('JDC-301', 'Ali Raza', '0333-5544333', 24.9312, 67.0822, True, 'JDC', 'Gulshan-e-Iqbal Base'),
                ('AMAN-401', 'Imran Bashir', '0321-4433221', 24.8211, 67.0344, True, 'Aman', 'Clifton / Boat Basin'),
                ('RESCUE-501', 'Kamran Akram', '0345-6677889', 24.9385, 67.0345, True, 'Rescue 1122', 'North Nazimabad Station'),
                ('EDHI-102', 'Rashid Khan', '0301-2233445', 24.8872, 67.1855, True, 'Edhi', 'Malir Sector Base'),
                ('CHHIPA-202', 'Nadeem Akhtar', '0313-7766554', 24.8415, 67.1235, True, 'Chhipa', 'Korangi Industrial Base'),
                ('JDC-302', 'Bilal Hussain', '0334-8899001', 24.8722, 67.0122, True, 'JDC', 'Lyari Sector Base')
            ])

        # Seed users if empty
        cursor.execute("SELECT COUNT(*) FROM public.users;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO public.users (username, password, role, vehicle_number) VALUES (%s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING;
            """, [
                ('admin', 'admin123', 'admin', None),
                ('admin1', 'password', 'admin', None),
                ('edhi101', 'password', 'driver', 'EDHI-101'),
                ('driver1', 'driver123', 'driver', 'EDHI-101'),
                ('chhipa201', 'password', 'driver', 'CHHIPA-201'),
                ('jdc301', 'password', 'driver', 'JDC-301'),
                ('rescue501', 'password', 'driver', 'RESCUE-501'),
                ('aman401', 'password', 'driver', 'AMAN-401')
            ])
        conn.commit()

    elif db_type == "sqlite":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'driver',
                vehicle_number TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                vehicle_number TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                organization TEXT NOT NULL DEFAULT 'Edhi',
                contact TEXT NOT NULL,
                current_lat REAL NOT NULL,
                current_lng REAL NOT NULL,
                is_available INTEGER NOT NULL DEFAULT 1,
                area_name TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                user_contact TEXT NOT NULL,
                emergency_type TEXT DEFAULT 'General Emergency',
                patient_lat REAL NOT NULL,
                patient_lng REAL NOT NULL,
                patient_address TEXT DEFAULT 'Karachi Location',
                assigned_vehicle TEXT,
                status TEXT NOT NULL DEFAULT 'Dispatched',
                distance_km REAL DEFAULT 0.0,
                eta_minutes INTEGER DEFAULT 5,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Seed users if empty
        cursor.execute("SELECT COUNT(*) FROM users;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO users (username, password, role, vehicle_number) VALUES (?, ?, ?, ?)
            """, [
                ('admin', 'password', 'admin', None),
                ('admin123', 'admin123', 'admin', None),
                ('edhi101', 'password', 'driver', 'EDHI-101'),
                ('driver1', 'driver123', 'driver', 'EDHI-101'),
                ('chhipa201', 'password', 'driver', 'CHHIPA-201'),
                ('jdc301', 'password', 'driver', 'JDC-301'),
                ('rescue501', 'password', 'driver', 'RESCUE-501'),
                ('aman401', 'password', 'driver', 'AMAN-401')
            ])

        # Seed drivers if empty
        cursor.execute("SELECT COUNT(*) FROM drivers;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO drivers (vehicle_number, name, organization, contact, current_lat, current_lng, is_available, area_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ('EDHI-101', 'Tariq Mehmood', 'Edhi', '0300-1122331', 24.8615, 67.0315, 1, 'Saddar Sector, Karachi'),
                ('CHHIPA-201', 'Mohammad Farooq', 'Chhipa', '0312-9988772', 24.8738, 67.0601, 1, 'PECHS / Nursery Station'),
                ('JDC-301', 'Ali Raza', 'JDC', '0333-5544333', 24.9312, 67.0822, 1, 'Gulshan-e-Iqbal Base'),
                ('AMAN-401', 'Imran Bashir', 'Aman', '0321-4433221', 24.8211, 67.0344, 1, 'Clifton / Boat Basin'),
                ('RESCUE-501', 'Kamran Akram', 'Rescue 1122', '0345-6677889', 24.9385, 67.0345, 1, 'North Nazimabad Station'),
                ('EDHI-102', 'Rashid Khan', 'Edhi', '0301-2233445', 24.8872, 67.1855, 1, 'Malir Sector Base'),
                ('CHHIPA-202', 'Nadeem Akhtar', 'Chhipa', '0313-7766554', 24.8415, 67.1235, 1, 'Korangi Industrial Base'),
                ('JDC-302', 'Bilal Hussain', 'JDC', '0334-8899001', 24.8722, 67.0122, 1, 'Lyari Sector Base')
            ])

        # Seed initial request if empty
        cursor.execute("SELECT COUNT(*) FROM emergency_requests;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO emergency_requests (user_name, user_contact, emergency_type, patient_lat, patient_lng, patient_address, assigned_vehicle, status, distance_km, eta_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ('Hamza Sheikh', '0300-9988771', 'Road Accident', 24.8625, 67.0540, 'Shahrah-e-Faisal near Baloch Colony', 'CHHIPA-201', 'Completed', 1.4, 4, '10:15 AM'),
                ('Zubair Ansari', '0333-1234567', 'Chest Pain / Heart Emergency', 24.9280, 67.0380, 'Block B, North Nazimabad', 'RESCUE-501', 'Completed', 1.1, 3, '11:30 AM')
            ])
        conn.commit()

    conn.close()

# Initialize DB on start
try:
    init_db()
except Exception as e:
    print(f"[DB INIT ERROR]: {e}")

# =============================================================================
# 2. HAVERSINE DISTANCE ALGORITHM (GPS SPHERICAL MATHEMATICS)
# =============================================================================
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Computes exact great-circle ground distance between two GPS coordinates
    in Kilometers taking Earth's curvature into account.
    """
    R = 6371.0  # Earth radius in KM
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

# =============================================================================
# 3. AI FIRST-AID ADVISOR INITIALIZATION
# =============================================================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
gemini_client = None
if GENAI_AVAILABLE:
    try:
        gemini_client = genai.Client(api_key=GEMINI_KEY)
    except Exception as e:
        print(f"[Gemini Client Warning]: {e}")


# =============================================================================
# 4. WEB ROUTES & API ENDPOINTS
# =============================================================================

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    for folder in [
        os.path.join(STATIC_DIR, 'assets'),
        STATIC_DIR,
        os.path.join(DIST_DIR, 'assets'),
        DIST_DIR
    ]:
        if os.path.exists(os.path.join(folder, filename)):
            return send_from_directory(folder, filename)
    return jsonify({"error": "Asset not found"}), 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend_spa(path):
    """
    Serves the modern emergency command center frontend.
    All dispatch, Leaflet mapping, live audio siren, and triage controls are rendered here.
    """
    # Prevent capturing API endpoints
    if path.startswith('api/'):
        return jsonify({"status": "error", "message": "API endpoint not found"}), 404

    # 1. First priority: templates/index.html (standard Flask folder)
    tpl_index = os.path.join(TEMPLATES_DIR, 'index.html')
    if (path == '' or path in ['driver', 'admin']) and os.path.exists(tpl_index):
        with open(tpl_index, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}

    # 2. Check static folders
    for static_root in [STATIC_DIR, DIST_DIR]:
        if os.path.exists(static_root):
            file_path = os.path.join(static_root, path)
            if path != '' and os.path.exists(file_path) and os.path.isfile(file_path):
                return send_from_directory(static_root, path)

    # 3. Check dist/index.html
    dist_index = os.path.join(DIST_DIR, 'index.html')
    if os.path.exists(dist_index):
        with open(dist_index, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}

    # 4. Fallback to pure HTML if templates/dist are missing
    return render_template_string(PATIENT_UI_TEMPLATE)

@app.route('/legacy-patient')
def legacy_patient_page():
    """Legacy Citizen SOS Emergency Portal."""
    return render_template_string(PATIENT_UI_TEMPLATE)

@app.route('/legacy-driver')
def legacy_driver_page():
    """Legacy Driver Mobile Console."""
    vehicle = session.get('vehicle_number', 'EDHI-101')
    return render_template_string(DRIVER_UI_TEMPLATE, vehicle_number=vehicle, username=session.get('username'))

@app.route('/legacy-admin')
def legacy_admin_page():
    """Legacy Admin Command & Control Center."""
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT vehicle_number, name, contact, is_available, organization, area_name FROM drivers;")
    drivers_list = cursor.fetchall()

    cursor.execute("""
        SELECT request_id, user_name, user_contact, assigned_vehicle, status, emergency_type, distance_km, eta_minutes, created_at 
        FROM emergency_requests 
        ORDER BY request_id DESC 
        LIMIT 20;
    """)
    requests_list = cursor.fetchall()
    conn.close()

    return render_template_string(ADMIN_UI_TEMPLATE, drivers=drivers_list, requests=requests_list, username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('serve_frontend_spa'))

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "engine": "Python 3 Flask",
        "team": ["Muhammad Anus", "Sufyan Akhter", "Rana Faraz Ahmed"]
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = (data.get('username') or '').strip().lower()
    password = (data.get('password') or '').strip()

    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgres":
        cursor.execute("SELECT user_id, username, role, vehicle_number FROM users WHERE LOWER(username) = %s AND password = %s;", (username, password))
    else:
        cursor.execute("SELECT user_id, username, role, vehicle_number FROM users WHERE LOWER(username) = ? AND password = ?;", (username, password))

    user = cursor.fetchone()
    conn.close()

    if user:
        # user can be tuple or sqlite Row
        u_id = user[0] if isinstance(user, tuple) else user["user_id"]
        u_name = user[1] if isinstance(user, tuple) else user["username"]
        u_role = user[2] if isinstance(user, tuple) else user["role"]
        u_veh = user[3] if isinstance(user, tuple) else user["vehicle_number"]

        session['user_id'] = u_id
        session['username'] = u_name
        session['role'] = u_role
        session['vehicle_number'] = u_veh

        return jsonify({
            "status": "success",
            "role": u_role,
            "username": u_name,
            "vehicle_number": u_veh
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Invalid Username or Password! Demo: admin / password or edhi101 / password"
        }), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    contact = (data.get('contact') or '').strip()
    organization = (data.get('organization') or 'Edhi').strip()
    vehicle_number = (data.get('vehicle_number') or '').strip().upper()
    username = (data.get('username') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not all([name, contact, organization, vehicle_number, username, password]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    try:
        if db_type == "postgres":
            cursor.execute("SELECT vehicle_number FROM drivers WHERE UPPER(vehicle_number) = %s;", (vehicle_number,))
        else:
            cursor.execute("SELECT vehicle_number FROM drivers WHERE UPPER(vehicle_number) = ?;", (vehicle_number,))

        if cursor.fetchone():
            conn.close()
            return jsonify({"status": "error", "message": "Vehicle number already registered"}), 400

        area_name = f"{organization} Standby Unit, Karachi"
        lat = 24.8615
        lng = 67.0315

        if db_type == "postgres":
            cursor.execute("""
                INSERT INTO drivers (vehicle_number, name, contact, current_lat, current_lng, is_available, organization, area_name)
                VALUES (%s, %s, %s, %s, %s, TRUE, %s, %s);
            """, (vehicle_number, name, contact, lat, lng, organization, area_name))
            cursor.execute("""
                INSERT INTO users (username, password, role, vehicle_number)
                VALUES (%s, %s, 'driver', %s);
            """, (username, password, vehicle_number))
        else:
            cursor.execute("""
                INSERT INTO drivers (vehicle_number, name, contact, current_lat, current_lng, is_available, organization, area_name)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?);
            """, (vehicle_number, name, contact, lat, lng, organization, area_name))
            cursor.execute("""
                INSERT INTO users (username, password, role, vehicle_number)
                VALUES (?, ?, 'driver', ?);
            """, (username, password, vehicle_number))

        conn.commit()
        conn.close()
        return jsonify({
            "status": "success",
            "driver": {
                "vehicle_number": vehicle_number,
                "name": name,
                "organization": organization,
                "contact": contact,
                "current_lat": lat,
                "current_lng": lng,
                "is_available": True,
                "area_name": area_name
            }
        })
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/fleet', methods=['GET'])
def get_fleet():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT vehicle_number, name, organization, contact, current_lat, current_lng, is_available, area_name FROM drivers;")
    rows = cursor.fetchall()
    conn.close()

    drivers = []
    for r in rows:
        drivers.append({
            "vehicle_number": r[0] if isinstance(r, tuple) else r["vehicle_number"],
            "name": r[1] if isinstance(r, tuple) else r["name"],
            "organization": r[2] if isinstance(r, tuple) else r["organization"],
            "contact": r[3] if isinstance(r, tuple) else r["contact"],
            "current_lat": float(r[4] if isinstance(r, tuple) else r["current_lat"]),
            "current_lng": float(r[5] if isinstance(r, tuple) else r["current_lng"]),
            "is_available": bool(r[6] if isinstance(r, tuple) else r["is_available"]),
            "area_name": r[7] if isinstance(r, tuple) else r["area_name"]
        })
    return jsonify({"status": "success", "drivers": drivers})

@app.route('/api/requests', methods=['GET'])
def get_requests():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT request_id, user_name, user_contact, emergency_type, patient_lat, patient_lng, patient_address, assigned_vehicle, status, distance_km, eta_minutes, created_at FROM emergency_requests ORDER BY request_id DESC LIMIT 25;")
    rows = cursor.fetchall()
    conn.close()

    reqs = []
    for r in rows:
        reqs.append({
            "request_id": r[0] if isinstance(r, tuple) else r["request_id"],
            "user_name": r[1] if isinstance(r, tuple) else r["user_name"],
            "user_contact": r[2] if isinstance(r, tuple) else r["user_contact"],
            "emergency_type": r[3] if isinstance(r, tuple) else r["emergency_type"],
            "patient_lat": float(r[4] if isinstance(r, tuple) else r["patient_lat"]),
            "patient_lng": float(r[5] if isinstance(r, tuple) else r["patient_lng"]),
            "patient_address": r[6] if isinstance(r, tuple) else r["patient_address"],
            "assigned_vehicle": r[7] if isinstance(r, tuple) else r["assigned_vehicle"],
            "status": r[8] if isinstance(r, tuple) else r["status"],
            "distance_km": float(r[9] if isinstance(r, tuple) else r["distance_km"]),
            "eta_minutes": int(r[10] if isinstance(r, tuple) else r["eta_minutes"]),
            "created_at": str(r[11] if isinstance(r, tuple) else r["created_at"])
        })
    return jsonify({"status": "success", "requests": reqs})

@app.route('/api/request/create', methods=['POST'])
def create_request():
    """Haversine Algorithmic Dispatch: finds closest free ambulance in Karachi."""
    data = request.json or {}
    user_name = data.get('name') or 'Emergency Citizen'
    user_contact = data.get('contact') or '0300-0000000'
    emergency_type = data.get('emergency_type') or 'General Emergency'
    address = data.get('address') or 'Karachi Location'

    try:
        p_lat = float(data.get('lat', 24.8607))
        p_lng = float(data.get('lng', 67.0011))
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Valid GPS coordinates required!"}), 400

    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgres":
        cursor.execute("SELECT vehicle_number, name, organization, contact, current_lat, current_lng, area_name FROM drivers WHERE is_available = TRUE;")
    else:
        cursor.execute("SELECT vehicle_number, name, organization, contact, current_lat, current_lng, area_name FROM drivers WHERE is_available = 1;")

    available_drivers = cursor.fetchall()

    if not available_drivers:
        conn.close()
        return jsonify({
            "status": "error",
            "message": "All Karachi ambulances are currently engaged on emergency calls! Please contact Edhi 115 or Chhipa 1020 directly."
        }), 400

    nearest_driver = None
    min_dist = float('inf')

    for d in available_drivers:
        v_num = d[0] if isinstance(d, tuple) else d["vehicle_number"]
        d_name = d[1] if isinstance(d, tuple) else d["name"]
        d_org = d[2] if isinstance(d, tuple) else d["organization"]
        d_contact = d[3] if isinstance(d, tuple) else d["contact"]
        d_lat = float(d[4] if isinstance(d, tuple) else d["current_lat"])
        d_lng = float(d[5] if isinstance(d, tuple) else d["current_lng"])
        d_area = d[6] if isinstance(d, tuple) else (d.get("area_name") if hasattr(d, "get") else "Karachi Station")

        dist = calculate_distance(p_lat, p_lng, d_lat, d_lng)
        if dist < min_dist:
            min_dist = dist
            nearest_driver = {
                "vehicle_number": v_num,
                "name": d_name,
                "organization": d_org,
                "contact": d_contact,
                "lat": d_lat,
                "lng": d_lng,
                "current_lat": d_lat,
                "current_lng": d_lng,
                "distance_km": round(dist, 2),
                "area_name": d_area
            }

    eta_minutes = max(2, round((min_dist / 25.0) * 60))
    time_str = datetime.now().strftime("%I:%M %p")

    if db_type == "postgres":
        cursor.execute("""
            INSERT INTO emergency_requests (user_name, user_contact, emergency_type, patient_lat, patient_lng, patient_address, assigned_vehicle, status, distance_km, eta_minutes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Dispatched', %s, %s) RETURNING request_id;
        """, (user_name, user_contact, emergency_type, p_lat, p_lng, address, nearest_driver['vehicle_number'], min_dist, eta_minutes))
        request_id = cursor.fetchone()[0]
        cursor.execute("UPDATE drivers SET is_available = FALSE WHERE vehicle_number = %s;", (nearest_driver['vehicle_number'],))
    else:
        cursor.execute("""
            INSERT INTO emergency_requests (user_name, user_contact, emergency_type, patient_lat, patient_lng, patient_address, assigned_vehicle, status, distance_km, eta_minutes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Dispatched', ?, ?, ?)
        """, (user_name, user_contact, emergency_type, p_lat, p_lng, address, nearest_driver['vehicle_number'], min_dist, eta_minutes, time_str))
        request_id = cursor.lastrowid
        cursor.execute("UPDATE drivers SET is_available = 0 WHERE vehicle_number = ?;", (nearest_driver['vehicle_number'],))

    conn.commit()
    conn.close()

    new_request_obj = {
        "request_id": request_id,
        "user_name": user_name,
        "user_contact": user_contact,
        "emergency_type": emergency_type,
        "patient_lat": p_lat,
        "patient_lng": p_lng,
        "patient_address": address,
        "assigned_vehicle": nearest_driver['vehicle_number'],
        "status": "Dispatched",
        "distance_km": round(min_dist, 2),
        "eta_minutes": eta_minutes,
        "created_at": time_str
    }

    return jsonify({
        "status": "success",
        "request": new_request_obj,
        "request_id": request_id,
        "driver": nearest_driver,
        "eta_minutes": eta_minutes
    })

@app.route('/api/request/update_status', methods=['POST'])
def update_status():
    data = request.json or {}
    req_id = data.get('request_id')
    new_status = data.get('status')

    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgres":
        cursor.execute("UPDATE emergency_requests SET status = %s WHERE request_id = %s RETURNING assigned_vehicle;", (new_status, req_id))
        row = cursor.fetchone()
        assigned_veh = row[0] if row else None
        if new_status in ('Completed', 'Cancelled') and assigned_veh:
            cursor.execute("UPDATE drivers SET is_available = TRUE WHERE vehicle_number = %s;", (assigned_veh,))
    else:
        cursor.execute("SELECT assigned_vehicle FROM emergency_requests WHERE request_id = ?;", (req_id,))
        row = cursor.fetchone()
        assigned_veh = row[0] if row else None
        cursor.execute("UPDATE emergency_requests SET status = ? WHERE request_id = ?;", (new_status, req_id))
        if new_status in ('Completed', 'Cancelled') and assigned_veh:
            cursor.execute("UPDATE drivers SET is_available = 1 WHERE vehicle_number = ?;", (assigned_veh,))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "new_status": new_status})

@app.route('/api/driver/toggle_status', methods=['POST'])
def toggle_driver_status():
    data = request.json or {}
    vehicle_number = data.get('vehicle_number')
    is_available = bool(data.get('is_available'))

    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgres":
        cursor.execute("UPDATE drivers SET is_available = %s WHERE vehicle_number = %s;", (is_available, vehicle_number))
    else:
        cursor.execute("UPDATE drivers SET is_available = ? WHERE vehicle_number = ?;", (1 if is_available else 0, vehicle_number))

    conn.commit()
    conn.close()
    return jsonify({"status": "updated", "vehicle_number": vehicle_number, "is_available": is_available})

@app.route('/api/demo/reset', methods=['POST'])
def reset_demo():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()
    if db_type == "postgres":
        cursor.execute("UPDATE drivers SET is_available = TRUE;")
    else:
        cursor.execute("UPDATE drivers SET is_available = 1;")
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Demo fleet reset to fully available"})

@app.route('/api/chatbot', methods=['POST'])
def first_aid_chatbot():
    """Emergency Medical Triage Advisor in Roman Urdu & English."""
    user_msg = (request.json or {}).get("message", "").strip()

    # Medical rule-based guidance in Roman Urdu & English
    lower = user_msg.lower()
    if any(k in lower for k in ['khoon', 'bleeding', 'blood']):
        reply = "⚠️ Zakhmi hissay par saaf patti ya kapra rakh kar lagatar mazbooti se dabayein (Direct Firm Pressure). Zakhmi hissay ko dil ki satah se ooper uthayein. Patti ko bar bar utha kar hargiz na dekhein. Ambulance pohanch rahi hai."
    elif any(k in lower for k in ['accident', 'hadsa', 'crash', 'chot']):
        reply = "⚠️ Mareez ko hargiz harkat na dein, khusoosan gardan aur kamar ko bilkul seedha rakhein taake spinal cord damage na ho. Agar helmet pehna hai to na utarein jab tak saans mein rukawat na ho. Bheerh hata dein."
    elif any(k in lower for k in ['chest', 'heart', 'dil', 'dard']):
        reply = "⚠️ Mareez ke collar aur belt dheeli karein. Mareez ko 45-degree angle par tek laga kar bithayein (Semi-Sitting Position). Mareez ko chalanay ya zor laganay na dein. Pur-sukoon rakhein."
    elif any(k in lower for k in ['saans', 'asthma', 'breath', 'dum']):
        reply = "⚠️ Mareez ko khuli hawa mein seedha bitha kar aage jhukayein. Agar asthma inhaler mojood ho to foran 2 puffs dein. Mareez ko letayein nahi, letne se saans mazeed ruk sakti hai."
    elif any(k in lower for k in ['behosh', 'unconscious', 'ghashi']):
        reply = "⚠️ Mareez ko aik karwat par litayein (Recovery Position) taake zaban ya ulti se saans ki naali band na ho. Mounh mein paani, dawa ya chamach hargiz na daalein."
    elif any(k in lower for k in ['fracture', 'haddi', 'toot']):
        reply = "⚠️ Tooti hui haddi ya jorh ko seedha karne ki koshish hargiz na karein. Usay aik gatta ya lakri baandh kar support (Splint) dein taake harkat na ho."
    elif any(k in lower for k in ['burn', 'jalna', 'aag']):
        reply = "⚠️ Jalay hue hissay par foran 15-20 minute tak narm taaza paani bahayein. Hargiz barf, toothpaste, haldi ya tail na lagayein. Chhalon (blisters) ko na phorein."
    elif any(k in lower for k in ['current', 'electric', 'bijli']):
        reply = "⚠️ Pehle main bijli ka switch band karein ya sookhi lakri se mareez ko alag karein. Khali haath mareez ko na chhuein. Agar saans band ho to foran CPR shuru karein."
    elif any(k in lower for k in ['choke', 'choking', 'phans', 'gala']):
        reply = "⚠️ Mareez ke dono kandhon ke darmiyan 5 martaba hath ki hatheli se thapki dein (Back Blows). Phir naaf ke ooper pait ko andar aur ooper dabayein (Heimlich Maneuver)."
    elif any(k in lower for k in ['saanp', 'snake', 'bite']):
        reply = "⚠️ Kaati hui jagah ko dil se neechay rakhein aur mareez ko bilkul sakin rakhein. Kaati hui jagah ko cheeray na lagayein aur choosne ki koshish na karein."
    elif any(k in lower for k in ['zeher', 'poison', 'chemical']):
        reply = "⚠️ Mareez ko zabardasti ulti (vomit) na karwayein, is se saans ki naali jal sakti hai. Chemical ka dabba ya label ambulance driver ke liye sanbhal kar rakhein."
    elif any(k in lower for k in ['heatstroke', 'garmi', 'dhoop']):
        reply = "⚠️ Mareez ko foran thandi chaon mein layeain. Gardan, baghal aur pait par geelay thanday kapray rakhein aur pankha chalayein."
    elif any(k in lower for k in ['bukhar', 'fever', 'jhatkay', 'fits']):
        reply = "⚠️ Mareez ke gird se sakht cheezein hata dein taake chot na lage. Mounh mein chamach ya kapra hargiz na daalein. Jhatkay rukne par aik karwat litayein."
    elif any(k in lower for k in ['delivery', 'pregnancy', 'dard-e-zeh']):
        reply = "⚠️ Maan ko saaf chadar par litayein aur gehri gehri saansein lene ko kahein. Haath aur tauliya saaf garm paani se dho kar paas rakhein. Ghabrayein nahi, ambulance raste mein hai."
    else:
        # Fallback to Gemini if online or default guidance
        if gemini_client:
            try:
                sys_instruction = (
                    "You are an emergency first-aid AI advisor for Madadgar Karachi ambulance dispatch. "
                    "Provide immediate, high-priority, actionable life-saving steps while the ambulance is en route. "
                    "Keep your response strictly under 3 short sentences. "
                    "If the user speaks in Roman Urdu, reply in Roman Urdu. "
                    "If English, reply in English. Start every response with ⚠️."
                )
                res = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_msg,
                    config=types.GenerateContentConfig(system_instruction=sys_instruction)
                )
                reply = res.text
            except Exception:
                reply = "⚠️ Mareez ko pur-sukoon rakhein, saans ki naali saaf rakhein aur zakhmi hissay ko harkat na dein. Karachi ambulance raste mein hai!"
        else:
            reply = "⚠️ Mareez ko pur-sukoon rakhein, saans ki naali saaf rakhein aur zakhmi hissay ko harkat na dein. Karachi ambulance raste mein hai!"

    return jsonify({"reply": reply})


# =============================================================================
# 5. CLEAN HTML / CSS / JS TEMPLATES
# =============================================================================

PATIENT_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Madadgar — Karachi Emergency Ambulance Dispatch</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Mapping Libraries (Free Open Engine) -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css" />
    <script src="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.js"></script>

    <style>
        :root {
            --primary: #c92a2a;
            --primary-dark: #a61e1e;
            --secondary: #1864ab;
            --dark: #212529;
            --light: #f8f9fa;
            --border: #dee2e6;
            --success: #2b8a3e;
        }
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: #f1f3f5; color: #212529; }
        
        /* Top Navigation Header */
        .header-bar {
            background: linear-gradient(135deg, #1c1f24 0%, #2b303a 100%);
            color: white;
            padding: 14px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid var(--primary);
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }
        .brand-title { display: flex; align-items: center; gap: 10px; }
        .brand-title h1 { margin: 0; font-size: 22px; font-weight: 800; letter-spacing: 0.5px; }
        .brand-title span { font-size: 13px; color: #ced4da; background: rgba(255,255,255,0.1); padding: 3px 8px; border-radius: 4px; }
        
        .header-actions { display: flex; align-items: center; gap: 12px; }
        .btn-portal-login {
            background: #228be6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-portal-login:hover { background: #1c7ed6; }

        /* Main Container */
        .container { max-width: 900px; margin: 20px auto; padding: 0 16px; }

        /* System Description Banner */
        .desc-banner {
            background: white;
            padding: 14px 20px;
            border-radius: 8px;
            border-left: 5px solid var(--primary);
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            font-size: 14px;
            line-height: 1.5;
            color: #495057;
        }

        /* Map Container */
        .map-card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 16px;
            border: 1px solid var(--border);
        }
        .map-card-header {
            padding: 10px 16px;
            background: #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            font-weight: 600;
        }
        #map { height: 380px; width: 100%; }

        /* Emergency Action Button */
        .btn-emergency {
            background: linear-gradient(135deg, #e03131 0%, #c92a2a 100%);
            color: white;
            border: none;
            padding: 18px 24px;
            width: 100%;
            font-size: 20px;
            font-weight: 800;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(201, 42, 42, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: transform 0.1s, box-shadow 0.2s;
        }
        .btn-emergency:hover { background: var(--primary-dark); box-shadow: 0 6px 20px rgba(201, 42, 42, 0.5); }
        .btn-emergency:active { transform: scale(0.99); }

        /* Status Assigned Card */
        .status-card {
            background: #fff5f5;
            border: 2px solid #ffc9c9;
            border-radius: 10px;
            padding: 18px 22px;
            margin-top: 16px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: none;
            animation: fadeIn 0.4s ease-in-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }

        .status-card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }
        .status-item {
            background: white;
            padding: 10px 14px;
            border-radius: 6px;
            border: 1px solid #ffd8a8;
        }
        .status-item span { display: block; font-size: 11px; text-transform: uppercase; color: #868e96; font-weight: 700; }
        .status-item strong { font-size: 16px; color: #212529; }

        /* First-Aid Section & Symptoms Dropdown */
        .first-aid-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .first-aid-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }
        .first-aid-header h3 { margin: 0; font-size: 17px; font-weight: 700; color: #1c7ed6; }

        .symptom-select-wrap {
            margin-bottom: 12px;
        }
        .symptom-select {
            width: 100%;
            padding: 10px 14px;
            border-radius: 6px;
            border: 1.5px solid #74c0fc;
            font-size: 14px;
            background: #f8f9fa;
            font-weight: 600;
            color: #1864ab;
            cursor: pointer;
        }
        .chat-box {
            height: 140px;
            overflow-y: auto;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 12px;
            font-size: 13.5px;
            line-height: 1.5;
        }
        .chat-msg-user { margin-bottom: 8px; color: #1864ab; font-weight: 600; }
        .chat-msg-ai { margin-bottom: 10px; background: #e7f5ff; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #339af0; color: #1971c2; }

        .chat-input-row { display: flex; gap: 8px; }
        .chat-input-row input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #ced4da;
            border-radius: 6px;
            font-size: 14px;
        }
        .chat-input-row button {
            background: #1864ab;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 700;
            cursor: pointer;
        }

        /* Footer */
        .footer {
            background: #1c1f24;
            color: #adb5bd;
            padding: 30px 20px;
            margin-top: 40px;
            border-top: 3px solid var(--primary);
            font-size: 13px;
            line-height: 1.6;
        }
        .footer-content { max-width: 900px; margin: auto; }
        .footer-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 24px;
            margin-bottom: 20px;
        }
        .footer-col h4 { color: white; margin-top: 0; margin-bottom: 10px; font-size: 15px; }
        .helpline-pill {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            color: #ffc9c9;
            padding: 4px 8px;
            border-radius: 4px;
            margin: 2px 4px 2px 0;
            font-size: 12px;
            font-weight: 700;
        }
        .team-box {
            background: rgba(255,255,255,0.06);
            padding: 12px 16px;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.15);
            color: #ced4da;
            font-size: 13.5px;
        }
        .team-box strong { color: #ffd43b; }
        .footer-bottom { text-align: center; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; color: #868e96; font-size: 12px; }

        /* Modal Popup */
        .modal { display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); }
        .modal-content {
            background: white;
            margin: 12% auto;
            padding: 24px;
            border-radius: 10px;
            max-width: 340px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .modal-content h3 { margin-top: 0; font-size: 18px; color: #212529; }
        .modal-content input {
            width: 100%;
            padding: 10px 12px;
            margin: 8px 0;
            border: 1.5px solid #ced4da;
            border-radius: 6px;
            font-size: 14px;
        }
        .modal-content button {
            width: 100%;
            padding: 10px;
            margin-top: 6px;
            border-radius: 6px;
            font-weight: 700;
            cursor: pointer;
            border: none;
        }
        .btn-submit-login { background: #2b8a3e; color: white; font-size: 15px; }
        .btn-cancel-login { background: #868e96; color: white; font-size: 13px; }
        .leaflet-routing-container { display: none !important; }
    </style>
</head>
<body>

<!-- Header Navigation -->
<div class="header-bar">
    <div class="brand-title">
        <h1>🚨 MADADGAR</h1>
        <span>Karachi Emergency Dispatch</span>
    </div>
    <div class="header-actions">
        <button class="btn-portal-login" onclick="openLoginModal()">🔑 Staff & Driver Login</button>
    </div>
</div>

<div class="container">
    <!-- Project Description Banner -->
    <div class="desc-banner">
        <strong>1-Click Emergency Ambulance Routing:</strong> Madadgar directly connects you to Karachi's nearest available welfare ambulance (Edhi, Chhipa, JDC, Aman, Rescue 1122). Our algorithmic engine locates your live GPS position and dispatches the closest vehicle within seconds.
    </div>

    <!-- Live Map -->
    <div class="map-card">
        <div class="map-card-header">
            <span>🗺️ Live Dispatch Map</span>
            <span id="locStatus" style="color:#2b8a3e;">📍 Detecting Location...</span>
        </div>
        <div id="map"></div>
    </div>

    <!-- Emergency Dispatch Trigger -->
    <button class="btn-emergency" onclick="requestAmbulance()">
        <span>🚑 REQUEST NEAREST AMBULANCE NOW</span>
    </button>

    <!-- Dispatch Status Card -->
    <div id="statusCard" class="status-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="margin:0; color:#c92a2a; font-size:18px;">🚑 Nearest Ambulance Dispatched!</h3>
            <span style="background:#2b8a3e; color:white; font-size:11px; padding:3px 8px; border-radius:4px; font-weight:700;">ON THE WAY</span>
        </div>
        
        <div class="status-card-grid">
            <div class="status-item">
                <span>Driver Name</span>
                <strong id="driverName">—</strong>
            </div>
            <div class="status-item">
                <span>Assigned Vehicle</span>
                <strong id="driverVehicle" style="color:#c92a2a;">—</strong>
            </div>
            <div class="status-item">
                <span>Driver Contact</span>
                <strong id="driverContact">—</strong>
            </div>
            <div class="status-item">
                <span>Estimated Distance & ETA</span>
                <strong id="driverDist" style="color:#1864ab;">Calculating ETA...</strong>
            </div>
        </div>
    </div>

    <!-- First-Aid Guidance with Rich Symptoms Dropdown -->
    <div class="first-aid-card">
        <div class="first-aid-header">
            <span>🛡️</span>
            <h3>Immediate First-Aid Guidance (While Waiting For Ambulance)</h3>
        </div>
        <p style="font-size:13px; color:#6c757d; margin-top:0; margin-bottom:10px;">
            Select a symptom from the dropdown below or type in Roman Urdu/English for step-by-step emergency care:
        </p>

        <!-- Dropdown for Common Emergency Situations -->
        <div class="symptom-select-wrap">
            <select id="symptomSelect" class="symptom-select" onchange="handleSymptomSelect()">
                <option value="">-- Choose Emergency Situation / علامت منتخب کریں --</option>
                <option value="Severe Bleeding / Shadeed Khoon Beh Raha Hai">🩸 Shadeed Khoon Beh Raha Hai (Severe Bleeding)</option>
                <option value="Road Accident / Motorcycle Crash / Hadsa">🚗 Road Accident / Motorcycle Crash (Hadsa)</option>
                <option value="Chest Pain / Dil Ka Daura (Cardiac Emergency)">💔 Seene Mein Shadeed Dard / Dil Ka Daura (Chest Pain)</option>
                <option value="Severe Asthma / Saans Lene Mein Dushwari">🫁 Saans Lene Mein Dushwari / Asthma Attack</option>
                <option value="Unconscious Patient / Mareez Behosh Hai">🧠 Mareez Behosh Hai (Unconscious / Unresponsive)</option>
                <option value="Bone Fracture / Haddi Tootna">🦴 Haddi Toot Gayi / Fracture & Joint Trauma</option>
                <option value="Severe Burns / Aag Se Jalna">🔥 Aag Se Jalna / Severe Burns & Scalds</option>
                <option value="Electric Shock / Bijli Ka Current">⚡ Bijli Ka Current Lagna (Electric Shock)</option>
                <option value="Choking / Gale Mein Cheez Phansna">🗣️ Gale Mein Cheez Phansna (Choking)</option>
                <option value="Snake Bite / Saanp Ka Kaatna">🐍 Saanp Ka Kaatna / Snake Bite</option>
                <option value="Poisoning / Zeher Ya Chemical Nigalna">🧪 Zeher Ya Chemical Nigalna (Poisoning)</option>
                <option value="Heatstroke / Shadeed Garmi Aur Chakkar">☀️ Heatstroke / Shadeed Garmi Aur Chakkar</option>
                <option value="High Fever & Fits / Bachon Mein Jhatkay">🌡️ Bachon Mein Tez Bukhar Aur Jhatkay (Fits)</option>
                <option value="Emergency Pregnancy / Delivery Pain">🤰 Emergency Pregnancy / Delivery Labor Pain</option>
            </select>
        </div>

        <div id="chatLog" class="chat-box">
            <div class="chat-msg-ai">⚠️ Emergency First-Aid Assistant is active. Please choose a situation above or type below for immediate guidance.</div>
        </div>

        <div class="chat-input-row">
            <input type="text" id="chatInput" placeholder="Type situation (e.g. 'bleed ho raha hai', 'fracture lag raha hai')...">
            <button onclick="sendChat()">Get Help</button>
        </div>
    </div>
</div>

<!-- Footer with Description, Helplines and Team Info -->
<div class="footer">
    <div class="footer-content">
        <div class="footer-grid">
            <div class="footer-col">
                <h4>About Madadgar System</h4>
                <p>Madadgar is Karachi's dedicated algorithmic emergency response dispatch system uniting independent welfare ambulance networks under a single real-time platform. By eliminating manual call center dispatch delays through GPS spherical matching, it protects patient survival during the critical Golden Hour.</p>
            </div>
            <div class="footer-col">
                <h4>24/7 Karachi Emergency Helplines</h4>
                <p>In case of system offline or severe mass casualties, reach welfare networks directly:</p>
                <div>
                    <span class="helpline-pill">Edhi: 115</span>
                    <span class="helpline-pill">Chhipa: 1020</span>
                    <span class="helpline-pill">JDC: 021-111-532-111</span>
                    <span class="helpline-pill">Aman: 1021</span>
                    <span class="helpline-pill">Rescue: 1122</span>
                </div>
            </div>
            <div class="footer-col">
                <h4>Project Engineering Team</h4>
                <div class="team-box">
                    <p style="margin:0 0 6px 0;"><strong>System Development & Architecture:</strong></p>
                    <p style="margin:0;">• Muhammad Anus</p>
                    <p style="margin:2px 0;">• Sufyan Akhter</p>
                    <p style="margin:0;">• Rana Faraz Ahmed</p>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            &copy; 2026 Madadgar Emergency Ambulance Dispatch System • Built with Python & Flask • Karachi, Pakistan
        </div>
    </div>
</div>

<!-- Login Modal -->
<div id="loginModal" class="modal">
    <div class="modal-content">
        <h3>Staff / Driver Authentication</h3>
        <p style="font-size:12px; color:#6c757d; margin-top:-5px;">Demo: admin / password or edhi101 / password</p>
        <input type="text" id="loginUser" placeholder="Username (e.g. admin or edhi101)">
        <input type="password" id="loginPass" placeholder="Password (password)">
        <button class="btn-submit-login" onclick="submitLogin()">Login</button>
        <button class="btn-cancel-login" onclick="closeLoginModal()">Cancel</button>
    </div>
</div>

<script>
    // Initialize Map with Karachi view
    var map = L.map('map').setView([24.8607, 67.0011], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    var userMarker, routingControl;
    var userLat = 24.8607, userLng = 67.0011;

    // Detect user coordinates
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(pos) {
            userLat = pos.coords.latitude;
            userLng = pos.coords.longitude;
            map.setView([userLat, userLng], 14);
            document.getElementById('locStatus').innerText = "📍 GPS Active: " + userLat.toFixed(4) + ", " + userLng.toFixed(4);
            userMarker = L.marker([userLat, userLng]).addTo(map).bindPopup("<b>Your Location (Patient)</b>").openPopup();
        }, function(err) {
            document.getElementById('locStatus').innerText = "📍 Saddar Central (Default)";
            userMarker = L.marker([userLat, userLng]).addTo(map).bindPopup("<b>Patient Location (Saddar Hub)</b>").openPopup();
        });
    }

    function openLoginModal() { document.getElementById('loginModal').style.display = 'block'; }
    function closeLoginModal() { document.getElementById('loginModal').style.display = 'none'; }

    function submitLogin() {
        var u = document.getElementById('loginUser').value.trim();
        var p = document.getElementById('loginPass').value.trim();

        if(!u || !p) {
            alert("Please enter username and password");
            return;
        }

        fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                if(data.role === 'admin') window.location.href = '/admin';
                else if(data.role === 'driver') window.location.href = '/driver';
            } else {
                alert(data.message || "Invalid credentials!");
            }
        })
        .catch(err => {
            alert("Network error. Please try again.");
        });
    }

    function requestAmbulance() {
        var emergencyType = document.getElementById('symptomSelect').value || 'General Emergency';
        
        fetch('/api/request/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: "Emergency Citizen",
                contact: "0300-1122334",
                emergency_type: emergencyType,
                lat: userLat,
                lng: userLng,
                address: "Karachi Central Sector"
            })
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                document.getElementById('statusCard').style.display = 'block';
                document.getElementById('driverName').innerText = data.driver.name + " (" + data.driver.organization + ")";
                document.getElementById('driverVehicle').innerText = data.driver.vehicle_number;
                document.getElementById('driverContact').innerText = data.driver.contact;
                document.getElementById('driverDist').innerText = data.driver.distance_km + " km (ETA: ~" + data.eta_minutes + " mins)";

                // Clear previous routing
                if (routingControl) map.removeControl(routingControl);

                // Draw live road routing
                routingControl = L.Routing.control({
                    waypoints: [L.latLng(userLat, userLng), L.latLng(data.driver.lat, data.driver.lng)],
                    routeWhileDragging: false,
                    addWaypoints: false,
                    draggableWaypoints: false,
                    fitSelectedRoutes: true,
                    lineOptions: { styles: [{ color: '#c92a2a', opacity: 0.85, weight: 6 }] }
                }).addTo(map);

                routingControl.on('routesfound', function(e) {
                    var summary = e.routes[0].summary;
                    document.getElementById('driverDist').innerText = (summary.totalDistance / 1000).toFixed(2) + " km (Live ETA: ~" + Math.round(summary.totalTime / 60) + " mins)";
                });

                // Scroll smoothly to status
                document.getElementById('statusCard').scrollIntoView({ behavior: 'smooth' });
            } else {
                alert(data.message || "Failed to dispatch ambulance.");
            }
        })
        .catch(err => {
            alert("Dispatch failed. Please check network connection.");
        });
    }

    function handleSymptomSelect() {
        var sel = document.getElementById('symptomSelect');
        var val = sel.value;
        if(!val) return;
        document.getElementById('chatInput').value = val;
        sendChat();
    }

    function sendChat() {
        var input = document.getElementById('chatInput');
        var msg = input.value.trim();
        if(!msg) return;

        var chatLog = document.getElementById('chatLog');
        chatLog.innerHTML += "<div class='chat-msg-user'><b>You:</b> " + msg + "</div>";
        chatLog.scrollTop = chatLog.scrollHeight;
        input.value = '';

        fetch('/api/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        })
        .then(res => res.json())
        .then(data => {
            chatLog.innerHTML += "<div class='chat-msg-ai'>" + data.reply + "</div>";
            chatLog.scrollTop = chatLog.scrollHeight;
        })
        .catch(err => {
            chatLog.innerHTML += "<div class='chat-msg-ai'>⚠️ Patient ko pursukoon rakhein aur ambulance ka intezar karein.</div>";
        });
    }
</script>

</body>
</html>
"""

DRIVER_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Driver Console — {{ vehicle_number }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #eef2f5; margin: 0; }
        .card { background: white; padding: 24px; border-radius: 10px; max-width: 500px; margin: 30px auto; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
        .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #dee2e6; padding-bottom: 12px; margin-bottom: 20px; }
        .card-header h2 { margin: 0; font-size: 20px; color: #212529; }
        .logout-link { color: #d9534f; font-weight: 700; text-decoration: none; font-size: 13px; }
        .status-box { background: #f8f9fa; border: 1.5px solid #ced4da; padding: 16px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
        .status-box h4 { margin: 0 0 6px 0; font-size: 13px; color: #6c757d; text-transform: uppercase; }
        .status-val { font-size: 24px; font-weight: 800; color: #2b8a3e; }
        .btn-toggle {
            width: 100%;
            padding: 14px;
            font-size: 16px;
            font-weight: 700;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            color: white;
            transition: all 0.2s;
        }
        .btn-toggle.free { background: #2b8a3e; }
        .btn-toggle.busy { background: #c92a2a; }
        .home-link { display: block; text-align: center; margin-top: 18px; color: #1864ab; font-size: 13px; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>

<div class="card">
    <div class="card-header">
        <h2>🚑 Driver Terminal</h2>
        <a href="/logout" class="logout-link">Logout</a>
    </div>
    <p>Logged In Driver: <strong>{{ username }}</strong></p>
    <p>Vehicle Number: <strong style="color:#c92a2a;">{{ vehicle_number }}</strong></p>

    <div class="status-box">
        <h4>Current Duty Status</h4>
        <div id="statusVal" class="status-val">AVAILABLE (FREE)</div>
    </div>

    <button id="toggleBtn" class="btn-toggle free" onclick="toggleStatus()">Click to Set: ON MISSION (BUSY)</button>

    <a href="/" class="home-link">← Return to Citizen Emergency Portal</a>
</div>

<script>
    var isFree = true;
    var vehicle = "{{ vehicle_number }}";

    function toggleStatus() {
        isFree = !isFree;
        var sVal = document.getElementById('statusVal');
        var btn = document.getElementById('toggleBtn');

        if(isFree) {
            sVal.innerText = "AVAILABLE (FREE)";
            sVal.style.color = "#2b8a3e";
            btn.innerText = "Click to Set: ON MISSION (BUSY)";
            btn.className = "btn-toggle free";
        } else {
            sVal.innerText = "ON MISSION (BUSY)";
            sVal.style.color = "#c92a2a";
            btn.innerText = "Click to Set: AVAILABLE (FREE)";
            btn.className = "btn-toggle busy";
        }

        fetch('/api/driver/toggle_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vehicle_number: vehicle, is_available: isFree })
        });
    }
</script>

</body>
</html>
"""

ADMIN_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Madadgar — Admin Command Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #f1f3f5; margin: 0; }
        .container { max-width: 1100px; margin: auto; }
        .card { background: white; padding: 22px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #dee2e6; }
        .header-card { display: flex; justify-content: space-between; align-items: center; }
        .header-card h2 { margin: 0; color: #212529; font-size: 22px; }
        .logout-link { color: #d9534f; font-weight: 700; text-decoration: none; font-size: 13px; }
        table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13.5px; }
        th, td { border: 1px solid #dee2e6; padding: 10px 12px; text-align: left; }
        th { background: #1864ab; color: white; font-weight: 600; }
        tr:nth-child(even) { background: #f8f9fa; }
        .badge-free { background: #2b8a3e; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
        .badge-busy { background: #c92a2a; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
        .home-btn { background: #e9ecef; color: #212529; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; font-weight: 600; }
    </style>
</head>
<body>

<div class="container">
    <div class="card header-card">
        <div>
            <h2>🏛️ Central Command & Control Center</h2>
            <p style="margin:4px 0 0 0; color:#6c757d; font-size:13px;">Logged In: <strong>{{ username }}</strong> (System Administrator)</p>
        </div>
        <div style="display:flex; gap:10px; align-items:center;">
            <a href="/" class="home-btn">← Home Portal</a>
            <a href="/logout" class="logout-link">Logout</a>
        </div>
    </div>

    <!-- Active Fleet Table -->
    <div class="card">
        <h3 style="margin-top:0; font-size:17px; color:#1864ab;">🚑 Karachi Welfare Ambulance Fleet Status</h3>
        <table>
            <tr>
                <th>Vehicle #</th>
                <th>Driver Name</th>
                <th>Welfare Organization</th>
                <th>Base Area</th>
                <th>Contact</th>
                <th>Status</th>
            </tr>
            {% for d in drivers %}
            <tr>
                <td><strong>{{ d[0] }}</strong></td>
                <td>{{ d[1] }}</td>
                <td><span style="font-weight:700; color:#c92a2a;">{{ d[4] }}</span></td>
                <td>{{ d[5] }}</td>
                <td>{{ d[2] }}</td>
                <td>
                    {% if d[3] %}
                        <span class="badge-free">Available (FREE)</span>
                    {% else %}
                        <span class="badge-busy">On Mission (BUSY)</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <!-- Emergency Requests Table -->
    <div class="card">
        <h3 style="margin-top:0; font-size:17px; color:#1864ab;">📋 Emergency Incidents Log (Haversine Dispatched)</h3>
        <table>
            <tr>
                <th>Req ID</th>
                <th>Patient Name</th>
                <th>Contact</th>
                <th>Emergency Condition</th>
                <th>Assigned Unit</th>
                <th>Distance</th>
                <th>ETA</th>
                <th>Status</th>
            </tr>
            {% for r in requests %}
            <tr>
                <td><strong>#{{ r[0] }}</strong></td>
                <td>{{ r[1] }}</td>
                <td>{{ r[2] }}</td>
                <td>{{ r[5] }}</td>
                <td><strong>{{ r[3] }}</strong></td>
                <td>{{ r[6] }} km</td>
                <td>~{{ r[7] }} mins</td>
                <td><span style="color:#c92a2a; font-weight:700;">{{ r[4] }}</span></td>
            </tr>
            {% endfor %}
        </table>
    </div>
</div>

</body>
</html>
"""

# =============================================================================
# 6. RUNNER
# =============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    print(f"============================================================")
    print(f" [MADADGAR FLASK SERVER] Running on http://127.0.0.1:{port}")
    print(f" Database: PostgreSQL ('emergency_db') with SQLite Local Fallback")
    print(f" Engineering Team: Muhammad Anus | Sufyan Akhter | Rana Faraz Ahmed")
    print(f"============================================================")
    app.run(host='127.0.0.1', port=port, debug=False)
