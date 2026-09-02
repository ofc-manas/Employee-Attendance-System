from flask import Flask, render_template , request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from zoneinfo import ZoneInfo
import os

IST = ZoneInfo("Asia/Kolkata")

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "attendance-system-secret-key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    role = db.Column(
        db.String(20),
        nullable=False,
        default="employee"
    )

    department = db.Column(db.String(100))

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    user = db.relationship("User", backref="attendances")

    date = db.Column(db.Date, nullable=False)

    check_in = db.Column(db.DateTime)

    check_out = db.Column(db.DateTime)

    working_hours = db.Column(db.Float, default=0)

    status = db.Column(
        db.String(20),
        default="Present"
    )

class Leave(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    user = db.relationship("User", backref="leaves")

    leave_type = db.Column(db.String(50))

    start_date = db.Column(db.Date)

    end_date = db.Column(db.Date)

    reason = db.Column(db.String(300))

    status = db.Column(
        db.String(20),
        default="Pending"
    )
class LeaveBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    total_leaves = db.Column(
        db.Integer,
        default=12
    )

    used_leaves = db.Column(
        db.Integer,
        default=0
    )

    remaining_leaves = db.Column(
        db.Integer,
        default=12
    )

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            # Clear any previous login session
            session.clear()

            # Store current user's information
            session["user_id"] = user.id
            session["role"] = user.role

            if user.role and user.role.lower() == "hr":
                return redirect(url_for("hr_dashboard"))

            return redirect(url_for("employee_dashboard"))

        flash("Invalid email or password.")

        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/employee/dashboard")
def employee_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only employees can access this page
    if session.get("role") != "employee":
        return "Access Denied", 403

    user_id = session["user_id"]

    user = db.session.get(User, user_id)

    today = date.today()

    attendance = Attendance.query.filter_by(
        user_id=user_id,
        date=today
    ).first()

    present_count = Attendance.query.filter_by(
        user_id=user_id,
        status="Present"
    ).count()

    return render_template(
        "employee_dashboard.html",
        user=user,
        present_count=present_count,
        absent_count=0,
        remaining_leaves=12,
        today=today,
        attendance=attendance
    )
@app.route("/attendance/history")
def attendance_history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only employees can access their attendance history
    if session.get("role") != "employee":
        return "Access Denied", 403

    user_id = session["user_id"]

    attendances = Attendance.query.filter_by(
        user_id=user_id
    ).order_by(
        Attendance.date.desc()
    ).all()

    return render_template(
        "attendance_history.html",
        attendances=attendances
    )
@app.route("/leave")
def leave_management():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only employees can access employee leave management
    if session.get("role") != "employee":
        return "Access Denied", 403

    user_id = session["user_id"]

    leave_balance = LeaveBalance.query.filter_by(
        user_id=user_id
    ).first()

    if not leave_balance:

        leave_balance = LeaveBalance(
            user_id=user_id,
            total_leaves=12,
            used_leaves=0,
            remaining_leaves=12
        )

        db.session.add(leave_balance)
        db.session.commit()

    leaves = Leave.query.filter_by(
        user_id=user_id
    ).order_by(
        Leave.start_date.desc()
    ).all()

    return render_template(
        "leave_management.html",
        leave_balance=leave_balance,
        leaves=leaves
    )

@app.route("/hr/leaves")
def hr_leave_management():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only HR can access this page
    if session.get("role") != "hr":
        return "Access Denied", 403

    # Get all leave requests
    leaves = Leave.query.order_by(
        Leave.start_date.desc()
    ).all()

    return render_template(
        "hr_leave_management.html",
        leaves=leaves
    )


@app.route("/hr/leave/approve/<int:leave_id>", methods=["POST"])
def approve_leave(leave_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "hr":
        return "Access Denied", 403

    leave = Leave.query.get_or_404(leave_id)

    if leave.status != "Pending":
        flash("This leave request has already been processed.")
        return redirect(url_for("hr_leave_management"))

    # Calculate number of leave days
    leave_days = (leave.end_date - leave.start_date).days + 1

    # Find employee's leave balance
    leave_balance = LeaveBalance.query.filter_by(
        user_id=leave.user_id
    ).first()

    # Create leave balance if it doesn't exist
    if not leave_balance:
        leave_balance = LeaveBalance(
            user_id=leave.user_id,
            total_leaves=12,
            used_leaves=0,
            remaining_leaves=12
        )

        db.session.add(leave_balance)

    # Check whether enough leaves are available
    if leave_days > leave_balance.remaining_leaves:
        flash("Employee does not have enough remaining leaves.")
        return redirect(url_for("hr_leave_management"))

    # Approve leave
    leave.status = "Approved"

    # Update leave balance
    leave_balance.used_leaves += leave_days
    leave_balance.remaining_leaves -= leave_days

    db.session.commit()

    flash("Leave request approved successfully.")

    return redirect(url_for("hr_leave_management"))



@app.route("/hr/leave/reject/<int:leave_id>", methods=["POST"])
def reject_leave(leave_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "hr":
        return "Access Denied", 403

    leave = Leave.query.get_or_404(leave_id)

    if leave.status != "Pending":
        flash("This leave request has already been processed.")
        return redirect(url_for("hr_leave_management"))

    leave.status = "Rejected"

    db.session.commit()

    flash("Leave request rejected.")

    return redirect(url_for("hr_leave_management"))


@app.route("/leave/apply", methods=["POST"])
def apply_leave():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only employees can apply for leave
    if session.get("role") != "employee":
        return "Access Denied", 403

    user_id = session["user_id"]

    leave_type = request.form["leave_type"]
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]
    reason = request.form["reason"]

    # Convert string dates to Python date objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # Check if end date is before start date
    if end_date < start_date:
        flash("End date cannot be before start date.")
        return redirect(url_for("leave_management"))

    # Calculate number of leave days
    leave_days = (end_date - start_date).days + 1

    # Get leave balance
    leave_balance = LeaveBalance.query.filter_by(
        user_id=user_id
    ).first()

    if not leave_balance:

        leave_balance = LeaveBalance(
            user_id=user_id,
            total_leaves=12,
            used_leaves=0,
            remaining_leaves=12
        )

        db.session.add(leave_balance)
        db.session.commit()

    # Check available leaves
    if leave_days > leave_balance.remaining_leaves:
        flash("You do not have enough leave balance.")
        return redirect(url_for("leave_management"))

    # Create leave request
    new_leave = Leave(
        user_id=user_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status="Pending"
    )

    db.session.add(new_leave)
    db.session.commit()

    flash("Leave application submitted successfully!")

    return redirect(url_for("leave_management"))

@app.route("/attendance/check-in", methods=["POST"])
def check_in():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only employees can check in
    if session.get("role") != "employee":
        return "Access Denied", 403

    user_id = session["user_id"]

    today = datetime.now(IST).date()

    existing_attendance = Attendance.query.filter_by(
        user_id=user_id,
        date=today
    ).first()

    if existing_attendance:
        flash("You have already checked in today.")
        return redirect(url_for("employee_dashboard"))

    attendance = Attendance(
        user_id=user_id,
        date=today,
        check_in=datetime.now(IST).replace(tzinfo=None),
        status="Present"
    )

    db.session.add(attendance)
    db.session.commit()

    flash("Check-in successful!")

    return redirect(url_for("employee_dashboard"))


@app.route("/attendance/check-out", methods=["POST"])
def check_out():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only employees can check out
    if session.get("role") != "employee":
        return "Access Denied", 403

    user_id = session["user_id"]

    today = datetime.now(IST).date()

    attendance = Attendance.query.filter_by(
        user_id=user_id,
        date=today
    ).first()

    if not attendance:
        flash("Please check in first.")
        return redirect(url_for("employee_dashboard"))

    if attendance.check_out:
        flash("You have already checked out today.")
        return redirect(url_for("employee_dashboard"))

    attendance.check_out = datetime.now(IST).replace(tzinfo=None)

    duration = attendance.check_out - attendance.check_in

    attendance.working_hours = round(
        duration.total_seconds() / 3600,
        2
    )

    db.session.commit()

    flash("Check-out successful!")

    return redirect(url_for("employee_dashboard"))

@app.route("/hr/dashboard")
def hr_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "hr":
        return "Access Denied", 403

    today = datetime.now(IST).date()

    # Total employees
    total_employees = User.query.filter_by(
        role="employee"
    ).count()

    # Get all employees
    employees = User.query.filter_by(
        role="employee"
    ).all()

    # Today's attendance records
    today_attendance = Attendance.query.filter_by(
        date=today
    ).all()

    # Create a dictionary for quick lookup
    attendance_map = {
        attendance.user_id: attendance
        for attendance in today_attendance
    }

    # Create attendance status for every employee
    attendance_data = []

    for employee in employees:

        attendance = attendance_map.get(employee.id)

        attendance_data.append({
            "employee": employee,
            "attendance": attendance
        })

    # Present employees
    present_today = Attendance.query.filter_by(
        date=today,
        status="Present"
    ).count()

    # Pending leave requests
    pending_leaves = Leave.query.filter_by(
        status="Pending"
    ).count()

    return render_template(
        "hr_dashboard.html",
        total_employees=total_employees,
        present_today=present_today,
        pending_leaves=pending_leaves,
        attendance_data=attendance_data,
        today=today
    )


@app.route("/hr/attendance")
def hr_attendance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "hr":
        return "Access Denied", 403

    # Get filter values from URL
    employee_id = request.args.get("employee_id")
    selected_date = request.args.get("date")

    # Get all employees
    employees = User.query.filter_by(role="employee").all()

    # Start attendance query
    query = Attendance.query

    # Filter by employee
    if employee_id:
        query = query.filter_by(user_id=int(employee_id))

    # Filter by date
    if selected_date:
        query = query.filter_by(
            date=datetime.strptime(selected_date, "%Y-%m-%d").date()
        )

    # Get attendance records
    attendances = query.order_by(
        Attendance.date.desc(),
        Attendance.check_in.desc()
    ).all()

    # Get employee names
    attendance_data = []

    for attendance in attendances:

        employee = User.query.get(attendance.user_id)

        attendance_data.append({
            "attendance": attendance,
            "employee": employee
        })

    return render_template(
        "hr_attendance.html",
        attendance_data=attendance_data,
        employees=employees,
        selected_employee=employee_id,
        selected_date=selected_date
    )
@app.route("/hr/employees")
def hr_employees():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "hr":
        return "Access Denied", 403

    # Get search text from URL
    search = request.args.get("search", "").strip()

    # Get employees
    query = User.query.filter_by(role="employee")

    # Apply search
    if search:
        query = query.filter(
            db.or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    employees = query.order_by(
        User.name.asc()
    ).all()

    return render_template(
        "hr_employees.html",
        employees=employees,
        search=search
    )


@app.route("/hr/employee/<int:user_id>")
def employee_details(user_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "hr":
        return "Access Denied", 403

    employee = User.query.filter_by(
        id=user_id,
        role="employee"
    ).first_or_404()

    attendances = Attendance.query.filter_by(
        user_id=user_id
    ).order_by(
        Attendance.date.desc()
    ).all()

    leaves = Leave.query.filter_by(
        user_id=user_id
    ).order_by(
        Leave.start_date.desc()
    ).all()

    leave_balance = LeaveBalance.query.filter_by(
        user_id=user_id
    ).first()

    return render_template(
        "employee_details.html",
        employee=employee,
        attendances=attendances,
        leaves=leaves,
        leave_balance=leave_balance
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        department = request.form["department"]
        role = request.form["role"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            department=department
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.")

        return redirect(url_for("login"))

    return render_template("register.html")
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
