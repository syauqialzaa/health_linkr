# health_linkr
🏥 Easily “connecting” patients with health services.

## models
| Model / Entity | Description | Examples of Key Fields |
| ------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------- |
| **User** | Basic entity for authentication (patient, doctor, staff). | username, email, password_hash, role |
| **PatientProfile** | Specific patient profile with basic medical data. | user (FK), full_name, birth_date, gender, phone |
| **DoctorProfile** | Doctor profile, specialty, practice schedule. | user (FK), specialty, qualification, clinic |
| **Clinic** | Clinic or department information where services are provided. | name, address, contact_number |
| **Service** | Type of service (consultation, vaccination, lab test, etc.). | name, description, duration_minutes, fee |
| **Appointment** | Service reservation between patient and doctor. | patient (FK), doctor (FK), service (FK), datetime, status |
| **ScheduleSlot** | Available time slot of doctor's practice. | doctor (FK), start_time, end_time, is_booked |
| **Role** | Access control—patient, doctor, staff/admin. | name, permissions |
| **Notification** | Notification (email/SMS/app) about appointment status. | user (FK), message, sent_at, read_flag |
| **SessionLog** | (Optional) Log of login sessions for security audits. | user (FK), login_time, logout_time, ip_address |
| **AuditTrail** | (Optional) Tracking of important data changes (e.g. cancel appt). | user (FK), action, model_name, timestamp |

## feature
| Features | Models / Entities Involved | Short Description |
| ------------------------------------------ | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 1. Authentication & Authentication | User, Role, SessionLog | • Registration, login/logout, reset password<br>• Role-based access (patient, doctor, staff/admin)<br>• Session logging for audit and security |
| 2. User Profile Management | PatientProfile, DoctorProfile, User | • Edit basic data (name, date of birth, gender, contact)<br>• Upload profile photo, manage doctor specialty details |
| 3. Clinic List & Details | Clinic | • View all clinics<br>• Clinic detail page (location, contact, description) |
| 4. Service Management | Service | • CRUD service type (consultation, vaccination, lab test)<br>• Set service duration & cost |
| 5. Doctor Slot Scheduling | ScheduleSlot, DoctorProfile | • Doctors create/manage practice time slots<br>• Show empty slots on booking page |
| 6. Appointment Booking & Management | Appointment, PatientProfile, DoctorProfile, Service, ScheduleSlot | • Patients select slots & services, then book<br>• Doctors/staff confirm, cancel, or mark as complete |
| 7. Real-Time Notification | Notification, User | • Send email/SMS or in-app notification when: booking is created, confirmed, canceled, or rescheduled |
| 8. My Appointment Dashboard | Appointment, PatientProfile | • List of patient appointment history with status (pending, confirmed, cancelled, completed) |
| 9. Clinic Team Management | Role, User, DoctorProfile | • Assign role “Clinic Admin” for clinic staff<br>• Admin can add/delete doctor or staff accounts |
| 10. Audit Trail & Tracking | AuditTrail, SessionLog | • Record important actions (create/cancel appointment, update profile)<br>• Track login/logout time and IP address |