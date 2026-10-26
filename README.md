# 🚨 Madadgar - Rapid Karachi Ambulance Dispatch System

Unified algorithmic emergency response dispatch system uniting Karachi's welfare ambulance fleets (Edhi, Chhipa, JDC, Aman, Rescue 1122).

**Developed by:**
- **Muhammad Anus**
- **Sufyan Akhter**
- **Rana Faraz Ahmed**

---

## 💻 How to Run on Your Laptop (100% Python Flask)

No **Node.js**, **npm**, or **TypeScript** required! The entire backend is built using **Python Flask (`app.py`)** connected to **PostgreSQL (`emergency_db`)**.

### Method 1: 1-Click Run (Easiest)
Double-click the **`run.bat`** file inside the project folder. It will automatically install dependencies and start the Flask server.

---

### Method 2: Command Prompt (CMD)

1. Open Command Prompt (CMD) and navigate to the project directory:
   ```cmd
   cd "C:\Users\anusj\Documents\Ambulance Project\Madadgar"
   ```

2. Install the required Python packages:
   ```cmd
   pip install -r requirements.txt
   ```

3. Start the server:
   ```cmd
   python app.py
   ```

4. Open your web browser and go to:
   👉 **http://127.0.0.1:5000**

---

## 🗄️ Database Setup (pgAdmin / PostgreSQL)

1. Open **pgAdmin 4** on your system.
2. Verify that the `emergency_db` database is created.
3. Right-click the database, open the **Query Tool**, and run the **`database.sql`** script.
4. The database password (`Ans@ri8088`) is pre-configured in `app.py`. If you need to change it, update the `PG_CONFIG` dictionary inside `app.py`.

---

## 🔑 Login Credentials

- **Admin Portal:**
  - Username: `admin` | Password: `password` (or `admin123`)
- **Driver Portal:**
  - Username: `edhi101` | Password: `password`
  - Username: `chhipa201` | Password: `password`
  - Username: `jdc301` | Password: `password`
