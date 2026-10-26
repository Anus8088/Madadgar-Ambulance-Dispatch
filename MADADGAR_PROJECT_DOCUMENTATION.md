# MADADGAR (مددگار) — Karachi Emergency Ambulance Dispatch System
## Complete End-to-End Technical & Architectural Documentation

---

## 1. Executive Summary

**MADADGAR** is a unified, real-time emergency welfare ambulance dispatch and triage platform tailored specifically for Karachi, Pakistan. 

In Karachi, municipal hospitals do not operate the city-wide ambulance network; instead, independent non-profit welfare organizations (**Edhi Foundation**, **Chhipa Welfare**, **JDC Welfare**, **Aman Health**, and **Rescue 1122**) handle over 90% of all emergency pre-hospital transports. 

Historically, this has created a fragmented emergency ecosystem:
- Bystanders and victims dial random hotlines (115, 1020, 1024, etc.) without knowing which organization has a vehicle closest to the accident site.
- Ambulances from different charities pass each other unnecessarily, wasting critical minutes ("Golden Hour").
- Average response times range between 25 to 45 minutes due to manual call routing and lack of GPS dispatch.

**Madadgar** solves this by unifying all welfare ambulances into a single GPS-driven algorithmic dispatch engine. Citizens can request an ambulance with one tap; the system instantly identifies the closest free ambulance across all participating organizations, computes a real road route via OpenStreetMap/OSRM, and notifies the citizen upon arrival while providing life-saving Gemini AI first-aid guidance.

---

## 2. System Architecture & Tech Stack

```
+---------------------------------------------------------------------------------+
|                                 CLIENT LAYER                                    |
|  +---------------------+  +----------------------+  +------------------------+  |
|  |   Citizen SOS       |  |   Driver Terminal    |  |  Admin Command Center  |  |
|  |  (Leaflet/OSRM Map) |  |  (Status & Nav Link) |  |  (Fleet KPIs & Logs)   |  |
|  +---------------------+  +----------------------+  +------------------------+  |
|           |                           |                          |              |
|           +---------------------------+--------------------------+              |
|                                       | (REST / JSON API)                       |
+---------------------------------------|-----------------------------------------+
                                        v
+---------------------------------------------------------------------------------+
|                                BACKEND SERVER                                   |
|                          Python 3 Flask API (`app.py`)                          |
|  +-------------------+  +--------------------+  +----------------------------+  |
|  |  /api/request/*   |  |  /api/fleet        |  |  /api/login & /register    |  |
|  |  Dispatch Engine  |  |  Fleet State Sync  |  |  RBAC Authentication       |  |
|  +-------------------+  +--------------------+  +----------------------------+  |
+---------------------------------------+-----------------------------------------+
                                        |
       +--------------------------------+-------------------------------+
       |                                |                               |
       v                                v                               v
+------------------+          +-------------------+          +--------------------+
|  OSRM Routing    |          |  OpenStreetMap    |          |  Gemini AI Triage  |
|  Road Navigation |          |  Free Map Tiles   |          |  First-Aid Advisor |
+------------------+          +-------------------+          +--------------------+
```

### Technology Matrix
| Layer | Technologies Used | Justification |
|---|---|---|
| **Frontend Framework** | React 18, TypeScript, Vite | High performance, strict type safety, zero runtime component crashes. |
| **Styling** | Tailwind CSS | Utility-first, responsive on mobile devices used by citizens and drivers. |
| **Mapping Engine** | Leaflet.js & OpenStreetMap (OSM) | 100% free, no credit card or Google Maps API billing limitations. |
| **Road Routing** | OSRM (Open Source Routing Machine) | Computes real driving road paths and turn geometries along Karachi roads. |
| **AI First-Aid Engine**| Google Gemini AI API (`@google/genai`) | Instant bilingual (Urdu/English) triage guidance during patient wait time. |
| **Backend & REST API** | Python 3 (Flask) & Node.js Proxy | Fast Python JSON API (`app.py`) for Haversine dispatch, fleet state, and auth. |
| **Audio Synthesizer**  | Web Audio API (`sirenAudio.ts`) | Synthetic dual-tone emergency siren & arrival chimes without external mp3s. |

---

## 3. End-to-End Application Modules

### 3.1. Citizen SOS Emergency Portal (`/`)
1. **Zero-Friction Geolocation:**
   - Detects live GPS coordinates via `navigator.geolocation`.
   - Allows tapping anywhere on the Karachi map or selecting one-tap Karachi hotspots (Saddar Empress Market, PECHS Tariq Road, Gulshan-e-Iqbal, Clifton, North Nazimabad, Malir).
2. **Emergency Condition Selector:**
   - Pre-configured emergency presets: *Road Accident (Hadsa)*, *Severe Bleeding (Khoon)*, *Cardiac / Chest Pain*, *Severe Burns / Fire*, *Breathing / Saans*, *Trauma / Unconscious*.
   - **"Other / Koi Aur Wajah":** Provides an **optional** text box so patients or attendants can type details if time permits, or immediately dispatch without typing a single letter.
3. **Algorithmic Nearest Dispatch:**
   - Calculates Euclidean & Haversine distance against all active units in the fleet.
   - Dispatches the single closest available ambulance regardless of organization.
4. **Live Road Tracking:**
   - The map draws the real driving route from the welfare base to the patient.
   - An animated single-unit ambulance marker travels smoothly along the road.
   - **No repetition/looping:** The vehicle travels once; upon arrival, the animation halts at the patient.
5. **Live Arrival Notification Alert:**
   - When the ambulance finishes the journey, a sound alert triggers and an emergency modal pops up:
     *"Ambulance Pohoch Chuki Hai! (Ambulance Has Arrived At Location)"*
   - Displays driver name, welfare trust name, and a 1-tap **"Call Driver Directly"** phone button.
6. **Gemini AI First-Aid Triage Assistant:**
   - Embedded sidebar providing instant medical guidance (e.g., CPR steps, burn cooling, wound pressure) while waiting for the vehicle.

---

### 3.2. Role-Based Access Control (RBAC) & Driver Registration
1. **Public vs. Protected Views:**
   - Citizen view is public.
   - `Driver Terminal` and `Admin Command` are locked behind authentication (`🔒 Driver`, `🔒 Admin`).
   - Unauthenticated clicks prompt the staff authentication modal.
2. **Sign In (Login):**
   - Clean, secure login with username and password.
   - Role verification on backend (`admin` vs `driver`).
3. **Driver Registration (Nayi Ambulance Registration):**
   - New drivers can onboard directly:
     - Driver Full Name
     - Welfare Organization selection (Edhi, Chhipa, JDC, Aman, Rescue 1122)
     - Vehicle Plate Number (e.g., `EDHI-105`)
     - Karachi Base Sector
     - Phone Number & Password
   - Successfully adding a vehicle inserts it into the live fleet database (`/api/register`) and redirects immediately to that vehicle's console.

---

### 3.3. Driver Mobile Terminal (`/driver`)
- Built specifically for mobile smartphone displays used by ambulance crews.
- **Assigned Mission Card:**
  - Emergency Category (with custom "Other" notes).
  - Patient Name & direct tap-to-call link (`tel:`).
  - Landmark Address & GPS Coordinates.
  - 1-Tap Google Maps Navigation redirect button (`https://www.google.com/maps/dir/?api=1...`).
- **Mission Lifecycle Controls:**
  - `En Route` ➔ `Arrived at Scene` ➔ `Transporting to Hospital` ➔ `Mission Completed (Free)`.
- **Driver Availability Switch:**
  - One-tap toggle between `FREE (Ready for Dispatch)` and `OFF DUTY / BUSY`.

---

### 3.4. Central Admin Command Dashboard (`/admin`)
- **Key Performance Indicators (KPIs):**
  - Total Fleet Size.
  - Active Emergency Missions.
  - Available Free Ambulances.
  - Average Dispatch Response Time (Minutes).
- **Live Fleet Control Grid:**
  - Shows every vehicle across Karachi with organization badge, driver contact, base sector, and live toggle.
- **Incident Log Table:**
  - Complete history of dispatches, timestamps, patient locations, assigned vehicles, and final statuses.
- **Pitch / Demo Simulation:**
  - Contains a simulation trigger to recreate real-world scenarios on demand for presentations.

---

## 4. API Endpoints Reference

| Method | Endpoint | Description | Payload / Params |
|---|---|---|---|
| `POST` | `/api/login` | Authenticates staff or driver credentials. | `{ username, password }` |
| `POST` | `/api/register` | Registers a new ambulance driver into the active fleet. | `{ name, username, password, organization, vehicle_number, area_name, contact }` |
| `GET` | `/api/fleet` | Returns all ambulance units, coordinates, and availability. | *None* |
| `GET` | `/api/requests` | Returns active and historical emergency dispatch records. | *None* |
| `POST` | `/api/request/create` | Algorithmic dispatch finding closest available vehicle. | `{ name, contact, lat, lng, emergency_type, address }` |
| `POST` | `/api/request/:id/status`| Updates an incident lifecycle state. | `{ status: "En Route" \| "Arrived" \| "Completed" }` |
| `POST` | `/api/driver/:vehicle_number/toggle` | Toggles driver availability state (`true`/`false`). | *None* |
| `POST` | `/api/ai/triage` | Queries Gemini AI model for bilingual first-aid advice. | `{ emergency_type, context }` |
| `POST` | `/api/demo/reset` | Resets demo data back to clean initial state. | *None* |

---

## 5. Security & Quality Assurance

1. **Defensive LatLng Sanitization:**
   - All latitude/longitude pairs are checked with `getValidLatLng()` to prevent `NaN` or `undefined` values from breaking map renderers.
2. **Animation Layer Isolation:**
   - Dedicated Leaflet `LayerGroup` prevents memory leaks and ensures exactly one ambulance marker exists during tracking.
3. **No External Secret Leaks:**
   - AI and backend keys are strictly isolated in server-side proxy routes.
4. **TypeScript Strict Typing:**
   - Full codebase compiles cleanly (`tsc --noEmit` and Vite build succeed with 0 errors).

---

## 6. How to Run & Present

1. **Development Server:**
   ```bash
   npm run dev
   ```
   Runs on `http://localhost:3000`.

2. **Testing Citizen SOS Flow:**
   - Open home page (`/`).
   - Select an emergency condition or click **"Other / Koi Aur Wajah"**.
   - Tap **"REQUEST NEAREST AMBULANCE NOW"**.
   - Watch the ambulance navigate along the road and inspect the **"Ambulance Pohoch Chuki Hai!"** modal on arrival.

3. **Testing Driver Flow:**
   - Click `🔒 Driver` tab in top navbar.
   - Sign in with an existing driver (`edhi101` / `password`) or click **"Register Driver"** to register a new vehicle.
   - View assigned mission and update status.

4. **Testing Admin Command Flow:**
   - Click `🔒 Admin` tab.
   - Log in with `admin` / `password`.
   - Monitor real-time KPIs, active missions, and fleet availability.
