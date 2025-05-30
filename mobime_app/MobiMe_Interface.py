from flask import Flask, render_template, request, redirect, send_file
import pyodbc
import csv
import io
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Used for form security and session management

# Function to connect to the SQL Server database
def get_db_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        #'SERVER=RAZERBLADE16;' # Main desktop computer / SQL server
        'SERVER=THINKPADZ16;'   # Sencond desktop computer / SQL server
        'DATABASE=MobiMe_Interface;'
        'Trusted_Connection=yes;'
    )

# Safe float parsing with fallback to 0.0
def parse_float(value):
    try:
        return float(value)
    except:
        return 0.0

# Ensure time string is properly formatted
def format_time(value):
    return value if value and ":" in value else None

# Route: Home page showing the form
@app.route("/", methods=["GET"])
def index():
    return render_combined_form()

# Route: Submit new entry
@app.route("/submit", methods=["POST"])
def submit():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Collect form data and prepare insert statement
    paid_hours = parse_float(request.form.get("paid", "0"))
    day_type = request.form.get("day_type", "Blank")

    cursor.execute("""
        INSERT INTO MobiMeData (
            Emp_Day_Code, Route_Activity_Code, Vehicle_Block_Code,
            Start_Site_Id, End_Site_Id,
            Start_Time_Military, End_Time_Military,
            Segment_Work_Time, Run_Work_Time,
            SON, SOFF, Paid_Hours, Day_Type, Created_At
        ) OUTPUT INSERTED.Record_Id
        VALUES (?, 'PARA', 'BLOCK1', ?, ?, ?, ?, '00:00', '00:00', ?, ?, ?, ?, ?)
    """, (
        request.form["duty"],
        request.form["start_site_id"],
        request.form["end_site_id"],
        request.form["start"],
        request.form["end"],
        format_time(request.form["son"]),
        format_time(request.form["soff"]),
        paid_hours,
        day_type,
        datetime.now()
    ))
    record_id = cursor.fetchone()[0]

    # Insert work type assignment
    cursor.execute("INSERT INTO WorkAssignment (Record_Id, Work_Type_Code) VALUES (?, ?)",
                   (record_id, request.form["type"]))

    # Insert selected days of the week
    for day in ['sun','mon','tue','wed','thu','fri','sat']:
        if request.form.get(day):
            cursor.execute("SELECT Day_Id FROM DayOfWeek WHERE Day_Name = ?", (day.capitalize(),))
            day_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO DayAssignment (Record_Id, Day_Id) VALUES (?, ?)", (record_id, day_id))

    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/")

# Route: Update existing entry
@app.route("/update/<int:record_id>", methods=["POST"])
def update(record_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update main record
    cursor.execute("""
        UPDATE MobiMeData SET
            Emp_Day_Code = ?, Start_Site_Id = ?, End_Site_Id = ?,
            Start_Time_Military = ?, End_Time_Military = ?,
            SON = ?, SOFF = ?, Paid_Hours = ?, Day_Type = ?
        WHERE Record_Id = ?
    """, (
        request.form["duty"],
        request.form["start_site_id"],
        request.form["end_site_id"],
        request.form["start"],
        request.form["end"],
        request.form["son"],
        request.form["soff"],
        parse_float(request.form.get("paid", "0")),
        request.form.get("day_type", "Blank"),
        record_id
    ))

    # Update work type
    cursor.execute("DELETE FROM WorkAssignment WHERE Record_Id = ?", (record_id,))
    cursor.execute("INSERT INTO WorkAssignment (Record_Id, Work_Type_Code) VALUES (?, ?)",
                   (record_id, request.form["type"]))

    # Update days of the week
    cursor.execute("DELETE FROM DayAssignment WHERE Record_Id = ?", (record_id,))
    for day in ['sun','mon','tue','wed','thu','fri','sat']:
        if request.form.get(day):
            cursor.execute("SELECT Day_Id FROM DayOfWeek WHERE Day_Name = ?", (day.capitalize(),))
            day_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO DayAssignment (Record_Id, Day_Id) VALUES (?, ?)", (record_id, day_id))

    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/")

# Route: Load data into form for editing
@app.route("/edit", methods=["POST"])
def edit():
    selected_ids = request.form.getlist("selected_ids")
    if len(selected_ids) != 1:
        return "Please select exactly one record to edit."

    record_id = selected_ids[0]
    conn = get_db_connection()
    cursor = conn.cursor()

    # Load full details for the selected row
    cursor.execute("""
        SELECT d.*, w.Work_Type_Code
        FROM MobiMeData d
        LEFT JOIN WorkAssignment w ON d.Record_Id = w.Record_Id
        WHERE d.Record_Id = ?
    """, (record_id,))
    row = cursor.fetchone()

    cursor.execute("SELECT Day_Id FROM DayAssignment WHERE Record_Id = ?", (record_id,))
    assigned_days = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT Site_Id, Site_Code FROM Site")
    sites = cursor.fetchall()

    cursor.execute("SELECT Work_Type_Code FROM WorkType")
    work_types = cursor.fetchall()

    # Load recent entries
    cursor.execute("""
        SELECT TOP 50 d.Record_Id, d.Emp_Day_Code, d.Start_Time_Military, d.End_Time_Military,
                      d.SON, d.SOFF, d.Paid_Hours, d.Day_Type,
                      s1.Site_Code AS StartSite, s2.Site_Code AS EndSite,
                      w.Work_Type_Code
        FROM MobiMeData d
        LEFT JOIN Site s1 ON d.Start_Site_Id = s1.Site_Id
        LEFT JOIN Site s2 ON d.End_Site_Id = s2.Site_Id
        LEFT JOIN WorkAssignment w ON d.Record_Id = w.Record_Id
        ORDER BY d.Record_Id DESC
    """)
    entries = cursor.fetchall()

    return render_template("form.html", row=row, assigned_days=assigned_days, sites=sites, work_types=work_types, entries=entries)

# Route: Delete selected entries
@app.route("/delete_selected", methods=["POST"])
def delete_selected():
    selected_ids = request.form.getlist("selected_ids")
    conn = get_db_connection()
    cursor = conn.cursor()
    for record_id in selected_ids:
        cursor.execute("DELETE FROM DayAssignment WHERE Record_Id = ?", (record_id,))
        cursor.execute("DELETE FROM WorkAssignment WHERE Record_Id = ?", (record_id,))
        cursor.execute("DELETE FROM MobiMeData WHERE Record_Id = ?", (record_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/")

# Route: Export selected or all records to CSV
@app.route("/export_csv", methods=["POST"])
def export_csv():
    selected_ids = request.form.getlist("selected_ids")
    conn = get_db_connection()
    cursor = conn.cursor()

    if selected_ids:
        format_ids = ','.join('?' for _ in selected_ids)
        query = f"SELECT * FROM MobiMeData WHERE Record_Id IN ({format_ids}) ORDER BY Record_Id DESC"
        cursor.execute(query, selected_ids)
    else:
        cursor.execute("SELECT * FROM MobiMeData ORDER BY Record_Id DESC")

    # Write to CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    columns = [desc[0] for desc in cursor.description]
    writer.writerow(columns)
    for row in cursor.fetchall():
        writer.writerow(row)

    output.seek(0)
    return send_file(io.BytesIO(output.read().encode()), mimetype="text/csv", as_attachment=True, download_name="MobiMeData.csv")

# Utility function: Renders the form with dropdown data and recent entries
def render_combined_form():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT Site_Id, Site_Code FROM Site")
    sites = cursor.fetchall()
    cursor.execute("SELECT Work_Type_Code FROM WorkType")
    work_types = cursor.fetchall()

    cursor.execute("""
        SELECT TOP 50 d.Record_Id, d.Emp_Day_Code, d.Start_Time_Military, d.End_Time_Military,
                      d.SON, d.SOFF, d.Paid_Hours, d.Day_Type,
                      s1.Site_Code AS StartSite, s2.Site_Code AS EndSite,
                      w.Work_Type_Code
        FROM MobiMeData d
        LEFT JOIN Site s1 ON d.Start_Site_Id = s1.Site_Id
        LEFT JOIN Site s2 ON d.End_Site_Id = s2.Site_Id
        LEFT JOIN WorkAssignment w ON d.Record_Id = w.Record_Id
        ORDER BY d.Record_Id DESC
    """)
    entries = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("form.html", sites=sites, work_types=work_types, entries=entries)

# Entry point for running the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5000)
