# 🚨 Madadgar - Rapid Karachi Ambulance Dispatch System

Unified algorithmic emergency response dispatch system uniting Karachi's welfare ambulance fleets (Edhi, Chhipa, JDC, Aman, Rescue 1122).

Developed by:
- **Muhammad Anus**
- **Sufyan Akhter**
- **Rana Faraz Ahmed**

---

## 💻 Apne Laptop Par Run Karne Ka Asaan Tareeqa (100% Python Flask)

Aapko kisi **Node.js**, **npm** ya **TypeScript** ki zaroorat nahi hai! Poora backend **Python Flask (`app.py`)** aur aapke **PostgreSQL (`emergency_db`)** par bana hua hai.

### Tareeqa 1: 1-Click Run (Sabse Asaan)
Project folder ke andar mojood **`run.bat`** file par double click karein!
Yeh khud-ba-khud dependencies install karega aur Flask server chala dega.

---

### Tareeqa 2: Command Prompt (CMD) Se Chalana

1. Apne laptop par Command Prompt (CMD) kholein aur project folder mein jayein:
   ```cmd
   cd "C:\Users\anusj\Documents\Ambulance Project\Madadgar"
   ```

2. Python packages install karein:
   ```cmd
   pip install -r requirements.txt
   ```

3. Server start karein:
   ```cmd
   python app.py
   ```

4. Ab browser mein yeh link kholein:
   👉 **http://127.0.0.1:5000**

---

## 🗄️ Database Setup (pgAdmin / PostgreSQL)

1. Apne laptop par **pgAdmin 4** kholein.
2. Verify karein ke `emergency_db` database mojood hai.
3. Database par right-click karke **Query Tool** kholein aur **`database.sql`** run karein.
4. `app.py` mein aapka password (`Ans@ri8088`) pehle se set hai! Agar aap change karna chahein to `app.py` mein `PG_CONFIG` ke andar apna password update kar sakte hain.

---

## 🔑 Login Credentials

- **Admin Portal:**
  - Username: `admin` | Password: `password` (ya `admin123`)
- **Driver Portal:**
  - Username: `edhi101` | Password: `password`
  - Username: `chhipa201` | Password: `password`
  - Username: `jdc301` | Password: `password`
