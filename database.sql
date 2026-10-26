-- =============================================================================
-- MADADGAR EMERGENCY AMBULANCE DISPATCH SYSTEM - DATABASE SCHEMA (POSTGRESQL)
-- Database Name: emergency_db
-- =============================================================================

-- 1. Create Tables if they don't already exist
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
    assigned_vehicle character varying(50) REFERENCES public.drivers(vehicle_number),
    status character varying(20) DEFAULT 'Pending',
    emergency_type character varying(100) DEFAULT 'General Emergency',
    patient_address text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.users (
    user_id SERIAL PRIMARY KEY,
    username character varying(50) NOT NULL UNIQUE,
    password character varying(50) NOT NULL,
    role character varying(20) NOT NULL,
    vehicle_number character varying(50)
);

-- 2. Alter existing tables if missing new columns (Safe Migration)
ALTER TABLE public.emergency_requests ADD COLUMN IF NOT EXISTS emergency_type character varying(100) DEFAULT 'General Emergency';
ALTER TABLE public.emergency_requests ADD COLUMN IF NOT EXISTS patient_address text;
ALTER TABLE public.drivers ADD COLUMN IF NOT EXISTS organization character varying(50) DEFAULT 'Edhi';
ALTER TABLE public.drivers ADD COLUMN IF NOT EXISTS area_name character varying(150);

-- 3. Seed / Update Karachi Welfare Ambulance Fleet
INSERT INTO public.drivers (vehicle_number, name, contact, current_lat, current_lng, is_available, organization, area_name)
VALUES 
  ('EDHI-101', 'Tariq Mehmood', '0300-1122331', 24.8615, 67.0315, true, 'Edhi', 'Saddar Sector, Karachi'),
  ('CHHIPA-201', 'Mohammad Farooq', '0312-9988772', 24.8738, 67.0601, true, 'Chhipa', 'PECHS / Nursery Station'),
  ('JDC-301', 'Ali Raza', '0333-5544333', 24.9312, 67.0822, true, 'JDC', 'Gulshan-e-Iqbal Base'),
  ('AMAN-401', 'Imran Bashir', '0321-4433221', 24.8211, 67.0344, true, 'Aman', 'Clifton / Boat Basin'),
  ('RESCUE-501', 'Kamran Akram', '0345-6677889', 24.9385, 67.0345, true, 'Rescue 1122', 'North Nazimabad Station'),
  ('EDHI-102', 'Rashid Khan', '0301-2233445', 24.8872, 67.1855, true, 'Edhi', 'Malir Sector Base'),
  ('CHHIPA-202', 'Nadeem Akhtar', '0313-7766554', 24.8415, 67.1235, true, 'Chhipa', 'Korangi Industrial Base'),
  ('JDC-302', 'Bilal Hussain', '0334-8899001', 24.8722, 67.0122, true, 'JDC', 'Lyari Sector Base')
ON CONFLICT (vehicle_number) DO UPDATE 
SET 
  organization = EXCLUDED.organization,
  area_name = EXCLUDED.area_name,
  is_available = true;

-- 4. Seed Default Users (Admin & Drivers)
INSERT INTO public.users (username, password, role, vehicle_number)
VALUES 
  ('admin', 'admin123', 'admin', NULL),
  ('driver1', 'driver123', 'driver', 'EDHI-101'),
  ('driver2', 'driver123', 'driver', 'CHHIPA-201'),
  ('edhi101', 'password', 'driver', 'EDHI-101')
ON CONFLICT (username) DO NOTHING;
