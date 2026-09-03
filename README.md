# Employee Attendance Management System

A web-based Employee Attendance Management System built using Flask and PostgreSQL. The application allows employees to manage their attendance and leave requests, while HR can monitor employees, attendance records, and leave applications through a dedicated HR dashboard.

## Live Demo

🌐 **Live Application:**  
https://employee-attendance-system-rose-psi.vercel.app/

---

## Features

### Employee Features

- Employee Registration
- Employee Login
- Secure Password Hashing
- Role-Based Authentication
- Employee Dashboard
- Attendance Check-In
- Attendance Check-Out
- Automatic Working Hours Calculation
- Attendance Status Tracking
- Attendance History
- Leave Management
- Leave Request Submission
- Leave Balance Tracking
- View Leave Request Status
- Logout

### HR Features

- HR Login
- HR Dashboard
- Total Employee Count
- Today's Attendance Overview
- Pending Leave Request Count
- Employee Attendance Monitoring
- Attendance History
- Employee Search
- Employee Details
- Employee Attendance Details
- Employee Leave Details
- Leave Request Management
- Approve Leave Requests
- Reject Leave Requests

### UI Features

- Responsive Design
- Bootstrap UI
- Glassmorphism Design
- Responsive Employee Dashboard
- Responsive HR Dashboard
- Status Badges
- Flash Messages
- Mobile-Friendly Layout

---

## Technologies Used

### Backend

- Python
- Flask
- Flask-SQLAlchemy
- Werkzeug
- Jinja2

### Database

- PostgreSQL

### Frontend

- HTML5
- CSS3
- Bootstrap
- Jinja2 Templates

### Deployment

- Vercel

### Other

- Python `datetime`
- Python `zoneinfo`
- Session-Based Authentication
- Environment Variables

---

# System Modules

## 1. Authentication Module

The authentication system provides login and registration functionality.

### Employee Registration

Employees can create an account by providing:

- Name
- Email
- Password
- Department
- Role

Passwords are securely hashed before being stored in the database.

### Login

Users log in using their email and password.

After successful authentication:

- Employees are redirected to the Employee Dashboard.
- HR users are redirected to the HR Dashboard.

---

# 2. Employee Dashboard

The Employee Dashboard provides employees with an overview of their attendance and leave information.

It displays:

- Employee name
- Total present days
- Total absent days
- Remaining leaves
- Today's attendance
- Check-in time
- Check-out time
- Working hours
- Attendance status

Employees can also:

- Check In
- Check Out
- View Attendance History
- Manage Leave Requests

---

# 3. Attendance Management

The attendance system allows employees to record their daily working time.

### Check-In

When an employee checks in:

1. The system verifies that the employee is logged in.
2. The system checks whether attendance has already been marked for the day.
3. The current Indian Standard Time (IST) is recorded.
4. The attendance status is set to `Present`.

### Check-Out

When an employee checks out:

1. The system verifies the employee's attendance record.
2. The current IST time is recorded.
3. Working hours are calculated automatically.

### Working Hours Calculation

Working hours are calculated using:

```text
Working Hours = Check-Out Time - Check-In Time
