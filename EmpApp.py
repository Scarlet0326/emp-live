from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__, template_folder='./templates')
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route('/')
def Index():
    if session.get("employee_id"):
        empid = session['employee_id']
        return render_template('/dash.html', empid=empid)

    else:
        return render_template('/login.html')

@app.route("/logout")
def logout():
    session['logged'] = False
    session["employee_id"] = []
    session["employee_name"] = []


    return render_template('/login.html')


@app.route("/registerEmployee")
def reg():
    return render_template('/signup.html')

# REGISTER AS A NEW EMPLOYEE, NOT AN ADMIN
@app.route("/Signup", methods=['POST'])
def signup():
    if request.method == 'POST' and 'employee_name' in request.form and 'employee_password' in request.form and 'employee_email' in request.form and 'employee_address' in request.form and 'employee_mobile' in request.form:
        # emp_id = request.form['emp_id']
        employee_name = request.form['employee_name']
        employee_email = request.form['employee_email']
        employee_password = request.form['employee_password']
        employee_address = request.form['employee_address']
        employee_mobile = request.form['employee_mobile']

    addEmployees = 'INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)'
    cursor = db_conn.cursor()

    try:
        cursor.execute(addEmployees,
                       ('', employee_name, employee_email, employee_password, employee_address, employee_mobile))
        db_conn.commit()
        emp_image_file_name_in_s3 = "emp-id-" + str(employee_name) + "_image_file"
        # s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            # s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            # bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            # s3_location = (bucket_location['LocationConstraint'])
            #
            # if s3_location is None:
            #     s3_location = ''
            # else:
            #     s3_location = '-' + s3_location
            #
            # object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            #     s3_location,
            #     custombucket,
            #     emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("Account register successfully")
    return render_template('/login.html')


# EMPLOYEE LOGIN PAGE
@app.route("/login", methods=['GET', 'POST'])
# Login function
def login():
    if request.method == 'POST' and 'employee_name' in request.form and 'employee_password' in request.form:
        # Create variables for easy access
        employee_name = request.form['employee_name']
        employee_password = request.form['employee_password']

        validateEmpAccount = "SELECT * FROM employee WHERE employee_name = '{}' AND employee_password = '{}'".format(
            employee_name,
            employee_password)
        cursor = db_conn.cursor()
        cursor.execute(validateEmpAccount)
        empAccount = cursor.fetchone()

        if empAccount:
            session['logged'] = True
            session['employee_id'] = empAccount[0]
            session['employee_name'] = empAccount[1]
            cursor.close()
            empid = session['employee_id']
            return render_template("/dash.html", empid=empid)
        else:
            msg = 'Incorrect username/password!'
        return render_template('/login.html', msg=msg)


# LIST OUT ALL THE EMPLOYEES
@app.route("/employee-list")
def listEmployee():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM emp")
    data = cursor.fetchall()
    cursor.close()
    return render_template("/employees-list.html", employee=data)


# ADD NEW EMPLOYEE TO DATABASE
@app.route("/addEmployee", methods=['POST'])
def addEmployee():
    if request.method == 'POST' and 'date' in request.form and 'emp_name' in request.form and 'emp_email' in request.form and 'emp_phone' in request.form and 'emp_jobs' in request.form:
        # emp_id = request.form['emp_id']
        date = request.form['date']
        emp_name = request.form['emp_name']
        emp_email = request.form['emp_email']
        emp_phone = request.form['emp_phone']
        emp_jobs = request.form['emp_jobs']

    addEmployees = "INSERT INTO emp VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    try:
        cursor.execute(addEmployees,
                       ('', date, emp_name, emp_email, emp_phone, emp_jobs))
        db_conn.commit()

    finally:
        cursor.close()

    print("Employee added successfully")
    return redirect(url_for('listEmployee'))


# RETRIEVE THE SPECIFIC EMPLOYEE DETAILS BEFORE GOING TO UPDATE
@app.route("/editEmployee/<employee_id>", methods=['POST', 'GET'])
def editEmp(employee_id):
    cursor = db_conn.cursor()
    cursor.execute('SELECT * FROM employee WHERE employee_id = %s', employee_id)
    details = cursor.fetchall()
    cursor.close()
    print(details[0])
    return render_template('/employee-list.html', employees=details[0])


# UPDATE THE EMPLOYEE DETAILS.AFTER UPDATED GO DIRECT BACK TO LIST ALL EMPLOYEE PAGE
@app.route("/updateEmployee/<emp_id>", methods=['POST', 'GET'])
def updateEmployee(emp_id):
    if request.method == 'POST':
        date = request.form['date']
        emp_name = request.form['emp_name']
        emp_email = request.form['emp_email']
        emp_phone = request.form['emp_phone']
        emp_jobs = request.form['emp_jobs']

    editEmployees = (
        "UPDATE emp SET date = %s, emp_name = %s,emp_email = %s, emp_phone = %s,emp_jobs = %s WHERE emp_id = %s"
    )
    cursor = db_conn.cursor()

    try:
        cursor.execute(editEmployees,
                       (date, emp_name, emp_email, emp_phone, emp_jobs,
                        emp_id))
    finally:
        db_conn.commit()
    print("UPDATE SUCCESSFULLY")

    return redirect(url_for('listEmployee'))


# DELETE THE SELECTED EMPLOYEE PROFILE
@app.route("/delete/<string:emp_id>", methods=['POST', 'GET'])
def deleteEmp(emp_id):
    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM emp WHERE emp_id = {0}".format(emp_id))
    db_conn.commit()
    cursor.close()
    flash('Employee Removed Successfully')
    return redirect(url_for('listEmployee'))



# LIST OUT ALL THE JOB
@app.route("/jobs-list")
def listJob():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM job")
    data = cursor.fetchall()
    cursor.close()
    return render_template("/jobs-list.html", job=data)


# ADD NEW JOB TO DATABASE
@app.route("/addJob", methods=['POST'])
def addJob():
    if request.method == 'POST' and 'date_j' in request.form and 'job' in request.form:
        # job_id = request.form['job_id']
        date_j = request.form['date_j']
        job = request.form['job']

    addJob = "INSERT INTO job VALUES (%s, %s, %s)"
    cursor = db_conn.cursor()

    try:
        cursor.execute(addJob,
                       ('', date_j, job))
        db_conn.commit()

    finally:
        cursor.close()

    print("Job added successfully")
    return redirect(url_for('listJob'))





# RETRIEVE THE SPECIFIC EMPLOYEE DETAILS BEFORE GOING TO UPDATE
@app.route("/editJob/<job_id>", methods=['POST', 'GET'])
def editJob(job_id):
    cursor = db_conn.cursor()
    cursor.execute('SELECT * FROM job WHERE job_id = %s', job_id)
    details = cursor.fetchall()
    cursor.close()
    print(details[0])
    return render_template('/jobs-list.html', job=details[0])


# UPDATE THE EMPLOYEE DETAILS.AFTER UPDATED GO DIRECT BACK TO LIST ALL EMPLOYEE PAGE
@app.route("/updateJob/<job_id>", methods=['POST', 'GET'])
def updateJob(job_id):
    if request.method == 'POST':
        date_j = request.form['date_j']
        job = request.form['job']

    editJob = (
        "UPDATE job SET date_j = %s, job = %s"
    )
    cursor = db_conn.cursor()

    try:
        cursor.execute(editJob,
                       (date_j, job))
    finally:
        db_conn.commit()
    print("UPDATE SUCCESSFULLY")

    return redirect(url_for('listJob'))


# DELETE THE SELECTED JOB PROFILE
@app.route("/deleteJob/<string:job_id>", methods=['POST', 'GET'])
def deleteJob(job_id):
    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM job WHERE job_id = {0}".format(job_id))
    db_conn.commit()
    cursor.close()
    flash('Job Removed Successfully')
    return redirect(url_for('listJob'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
