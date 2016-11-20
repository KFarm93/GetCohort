#Import and load dotenv folder for python to easily set environment variables
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
# # We'll render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will help us to send/show on the
# browser the file that the user just uploaded
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory
import pg, os, random, string
from werkzeug import secure_filename

# Database credentials for local Database
db = pg.DB(
    dbname=os.environ.get("PG_DBNAME"),
    host=os.environ.get("PG_HOST"),
    user=os.environ.get("PG_USERNAME"),
    passwd=os.environ.get("PG_PASSWORD")
)

db.debug = True

tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
# Initialize the Flask application
app = Flask("Get Cohort", template_folder = tmp_dir)
# Link to the images folder in the static folder
images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/images')
app.config['UPLOAD_FOLDER'] = images_dir
# These are the extensions that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# Secret Key to generate encrypted tokens used to verify identity
app.secret_key = os.environ.get("SECRET_KEY")

# For a given file, return whether it's an allowed type or not(images)
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

        

# This route will perform a request to execute given request and update
# the value of the operation
@app.route('/')
def home():
    student_query = db.query('''
        select
        	users.id,
        	first_name,
        	last_name,
        	cohort.name as cohort
        from
        	users,
        	users_link_cohort,
        	cohort,
        	users_link_type,
        	user_type
        where
        	users.id = users_link_type.user_id and
        	users_link_type.user_type_id = user_type.id and
        	users.id = users_link_cohort.user_id and
        	users_link_cohort.cohort_id = cohort.id and
            user_type.type = 'Student' and
            cohort.name = 'September 2016'
        ;
    '''
    )
    instructor_query = db.query('''
        select
        	users.id,
        	first_name,
        	last_name,
        	cohort.name as cohort
        from
        	users,
        	users_link_cohort,
        	cohort,
        	users_link_type,
        	user_type
        where
        	users.id = users_link_type.user_id and
        	users_link_type.user_type_id = user_type.id and
        	users.id = users_link_cohort.user_id and
        	users_link_cohort.cohort_id = cohort.id and
            user_type.type = 'Instructor' and
            cohort.name = 'September 2016'
        ;
    '''
    )
    student_result_list = student_query.namedresult()
    instructor_result_list = instructor_query.namedresult()
    if 'email' in session:
        return render_template(
            "index.html",
            student_result_list = student_result_list,
            instructor_result_list = instructor_result_list
        )
    else:
        return render_template (
            "index_landing.html"
        )

# Route for All Students page to generate data based on query request
@app.route('/all_students', methods=["POST", "GET"])
def all_students():
    query_cohort_name = db.query("select name from cohort;")
    cohort_list = query_cohort_name.namedresult()
    cohort_name = request.form.get('cohort_name')
    query = db.query('''
        select
        	users.id,
        	first_name,
        	last_name,
            avatar,
        	cohort.name
        from
        	users,
        	users_link_cohort,
        	cohort,
        	users_link_type,
        	user_type
        where
        	users.id = users_link_type.user_id and
        	users_link_type.user_type_id = user_type.id and
        	users.id = users_link_cohort.user_id and
        	users_link_cohort.cohort_id = cohort.id and
        	cohort.name = $1 and user_type.type = 'Student'
        ;
    ''', cohort_name
    )
    result_list = query.namedresult()
    return render_template(
        "all_students.html",
        result_list = result_list,
        cohort_list = cohort_list,
    )

# Route to generate user profile info for ids from query
@app.route('/profile/<id>')
def profile(id):
    query = db.query('''
        select
        	id,
        	first_name,
        	last_name,
        	email,
        	web_page,
        	github,
        	bio,
            avatar,
        	users.password,
            current_location
        from
        	users
        where users.id = $1;
    ''', id)
    result_list = query.namedresult()
    project_query = db.query('''
        select
            project.name,
            project.id
        from
            users,
            users_link_project,
            project
        where
            users.id = users_link_project.users_id and users_link_project.project_id = project.id and
            users.id = $1;
    ''', id).namedresult()
    skill_query = db.query('''
        select
            name,
            skill.id
        from
            users,
            users_link_skill,
            skill
        where
            users.id = users_link_skill.users_id and users_link_skill.skill_id = skill.id and users.id = $1;
    ''', id).namedresult()
    return render_template(
        "profile.html",
        user = result_list[0],
        project_query = project_query,
        skill_query = skill_query
    )

# Delete user info, then send back to All Students
@app.route("/delete", methods=["POST"])
def delete():
    id = request.form.get("id")
    db.delete(
        "users", {
        "id": id
        }
    )
    return redirect("/all_students")

# Route handler to send user to Update entry
@app.route("/update", methods=["POST"])
def update():
    # email = request.form.get("email")
    user_id = request.form.get("id")
    query_student = db.query("select * from users where id = $1", user_id)
    query_project_name = db.query("""
    select
        id,
        name
    from
        project;
    """).namedresult()
    query_skill_name = db.query("""
    select
        id,
        name
    from
        skill
    """).namedresult()
    result_list = query_student.namedresult()
    return render_template(
        "update.html",
        result = result_list[0],
        user_id = user_id,
        query_project_name = query_project_name,
        query_skill_name = query_skill_name
    )

# Route handler to actually Update User info, queries info in database
@app.route("/update_entry", methods=["POST"])
def update_entry():
    user_id = request.form.get("id")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    web_page = request.form.get("web_page")
    github = request.form.get("github")
    bio = request.form.get("bio")
    project = request.form.getlist("project_name")
    skill = request.form.getlist("skill_name")

    db.update(
        "users", {
            "id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "web_page": web_page,
            "github": github,
            "bio": bio
            }
        )

    if skill:
        skill_query = db.query ("""
        select
        	skill_id
        from
        	users_link_skill
        where
        	users_id = $1;
        """, user_id).namedresult()
        not_skill_list = []
        add_skill_list = []
        for i in skill:
            for entry in skill_query:
                if int(i) in entry:
                    not_skill_list.append(int(i))
                else:
                    pass
            add_skill_list.append(int(i))
            skill_to_add = list(set(add_skill_list)^set(not_skill_list))
        for r in skill_to_add:
            db.insert(
                "users_link_skill",
                users_id = user_id,
                skill_id = r
            )

    if project:
        project_query = db.query ("""
        select
        	project_id
        from
        	users_link_project
        where
        	users_id = $1;
        """, user_id).namedresult()
        not_project_list = []
        add_project_list = []
        for i in project:
            for entry in project_query:
                if int(i) in entry:
                    not_project_list.append(int(i))
                else:
                    pass
            add_project_list.append(int(i))
            project_to_add = list(set(add_project_list)^set(not_project_list))
        for r in project_to_add:
            db.insert(
                "users_link_project",
                users_id = user_id,
                project_id = r
            )


    return redirect('/')

# Route handler to add user to database and site
@app.route("/add")
def add():
    query_cohort_name = db.query("""
    select
    	cohort.id,
    	name
    from
    	cohort;
    """).namedresult()

    query_user_type = db.query("""
    select
        id,
        type
    from
        user_type;
    """).namedresult()

    return render_template(
        "add.html",
        query_cohort_name=query_cohort_name,
        query_user_type=query_user_type
    )
# Route handler to enter Add User Info in form as well as database
@app.route("/add_entry", methods=["POST"])
def add_entry():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    web_page = request.form.get("web_page")
    github = request.form.get("github")
    company_name = request.form.get("company_name")
    current_location = request.form.get("current_location")
    available_for_work = request.form.get("available_for_work")
    bio = request.form.get("bio")
    cohort_id = request.form.get("cohort_id")
    user_type_id = request.form.get("user_type_id")
    # insert user info to database
    db.insert (
        "users",
        first_name = first_name,
        last_name = last_name,
        email = email,
        web_page = web_page,
        github = github,
        current_location = current_location,
        available_for_work = available_for_work,
        bio = bio
    )

    query_new_entry = db.query("select id from users where email = $1", email)
    result_list = query_new_entry.namedresult()
    user_id = result_list[0].id

    db.insert (
        "users_link_type",
        user_id = user_id,
        user_type_id = user_type_id
    )
    if company_name:
        db.insert(
            "company",
            name = company_name
        )
        company_query = db.query("select id from company where name = $1", company_name).namedresult()
        company_id = company_query[0].id
        db.insert(
            "users_link_company",
            user_id = user_id,
            company_id = company_id
        )
    else:
        pass

    query_user_type = db.query("""
    select
        users.id
    from
    	users,
    	users_link_type,
    	user_type
    where
    	users.id = users_link_type.user_id and
    	users_link_type.user_type_id = user_type.id and
    	(user_type.type = 'Student' or user_type.type = 'Instructor')
    """)
    user_result_list = query_user_type.namedresult()
    for entry in user_result_list:
        if user_id in entry:
            db.insert (
                "users_link_cohort",
                user_id = user_id,
                cohort_id = cohort_id
            )
        else:
            pass

    return redirect("/all_students")

# this route will allow user to login to site and their account
@app.route("/submit_login", methods=["POST"])
def submit_login():
    email = request.form.get('email')
    password = request.form.get('password')
    query = db.query("select * from users where email = $1", email)
    admin_query = db.query('''
    select
    	users.email,
    	user_type.type
    from
    	users,
    	users_link_type,
    	user_type
    where
    	users.id = users_link_type.user_id and
    	users_link_type.user_type_id = user_type.id
    	and user_type.type = 'Admin';
    ''')
    result_list = query.namedresult()
    admin_list = admin_query.namedresult()
    if len(result_list) > 0:
        user = result_list[0]
        if user.password == password:
            session['first_name'] = user.first_name
            session['email'] = user.email
            session['id'] = user.id
            session['avatar'] = user.avatar
            #new session variable
            for entry in admin_list:
                if entry.email == session['email']:
                    session['is_admin'] = True
                else:
                    session['is_admin'] = False
            flash("%s, you have successfully logged into the application" % session["first_name"])
            return redirect('/profile/%d' % user.id)
        else:
            return redirect("/")
    else:
        return redirect("/")

# Submits request for user to login
@app.route("/submit_logout", methods = ["POST"])
def submit_logout():
    del session['first_name']
    del session['email']
    del session['id']
    del session['is_admin']
    return redirect("/")

# Search bar for specifc user
@app.route("/search_user", methods=["POST"])
def search_user():
    name = request.form.get('search_bar')
    split_name = name.split()
    name_length = len(name)
    split_name_length = len(split_name)
    first_name_to_search = "%"+split_name[0]+"%"
    if name_length >= 3:
        if split_name_length >= 2:
            last_name_to_search = "%"+split_name[1]+"%"
            query = db.query("select * from users where (first_name ilike $1 or last_name ilike $2)", (first_name_to_search, last_name_to_search))
            result_list = query.namedresult()
            if len(result_list) == 1:
                print result_list
                return redirect('/profile/%d' % result_list[0].id)
            elif len(result_list) >= 2:
                return render_template(
                    "disambiguation.html",
                    result_list = result_list
                    )
            else:
                return redirect('/')

        elif split_name_length <= 1:
            query = db.query("select * from users where (first_name ilike $1 or last_name ilike $1)", first_name_to_search)
            result_list = query.namedresult()
            if len(result_list) == 1:
                return redirect('/profile/%d' % result_list[0].id)
            elif len(result_list) >= 2:
                return render_template(
                    "disambiguation.html",
                    result_list = result_list
                    )
            else:
                return redirect('/')
    else:
        return redirect('/')

# Renders All Projects listed in database
@app.route("/all_projects")
def all_projects():
    query = db.query("select * from project;")
    project_list = query.namedresult()
    return render_template(
        "all_projects.html",
        project_list = project_list
    )

# Project profile lists that project, info regarding project, skills/technology used, as well as team members on project
@app.route("/project_profile/<id>")
def project_profile(id):
    query_projects = db.query("select * from project where id = $1;", id)
    project_list = query_projects.namedresult()
    query_skills = db.query("""
        select
        	project.id as project_identifier,
        	project.name as project_name,
        	project.link,
        	project.image,
        	project.description,
        	skill.id as skill_identifier,
        	skill.name as skill_name,
        	project_link_skill.project_id,
        	project_link_skill.skill_id
        from
            project,
            skill,
            project_link_skill
        where
        	project.id = project_link_skill.project_id and
        	skill.id = project_link_skill.skill_id and
        	project.id = $1
        ;""", id)
    skills = query_skills.namedresult()
    query_contributors = db.query("""
        select
            users.id,
            users.first_name,
            users.last_name,
            project.name as project_name,
            users_link_project.users_id as users_link_id,
            users_link_project.project_id as project_link_id
        from
            users,
            project,
            users_link_project
        where
            users.id = users_link_project.users_id and
            project.id = users_link_project.project_id and
            project.id = $1
        ;""", id)
    contributors = query_contributors.namedresult()
    query_contributors_id = db.query("""
        select
            users.id
        from
            users,
            project,
            users_link_project
        where
            users.id = users_link_project.users_id and
            project.id = users_link_project.project_id and
            project.id = $1
        ;""", id)
    contributors_id = query_contributors_id.namedresult()
    query_project_images = db.query("""
        select
        	project.id as project_id,
        	image.id as image_id,
        	image.image,
            image.description
        from
            project,
            image
        where
            project.id = image.project_id and
            project.id = $1
        ;
        """, id)
    project_images = query_project_images.namedresult()
    return render_template(
        "project_profile.html",
        project = project_list[0],
        skills = skills,
        contributors = contributors,
        contributors_id_list = contributors_id,
        images_information = project_images
    )

@app.route("/skill_profile/<id>")
def skill_profile(id):
    skill = db.query("select name from skill where id = $1", id).namedresult()
    practitioners = db.query("""
    select
    	first_name,
    	last_name,
        users.id
    from
    	users,
    	users_link_skill,
    	skill
    where
    	users.id = users_link_skill.users_id and
    	users_link_skill.skill_id = skill.id and
    	skill.id = $1;
    """, id).namedresult()
    return render_template(
        "skill.html",
        skill = skill[0],
        practitioners = practitioners
    )

# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    file_name_size = 64
    user_id = request.form.get("id")
    print "user id %s\n\n\n" % user_id
    project_id = request.form.get("project_id")
    print "project id %s\n\n\n" % project_id
    # Get the name of the uploaded file
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1]
        # Create new random name for the file using letters and digits
        filename = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(file_name_size)]) + "." + file_extension
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Redirect the user to the uploaded_file route, which
        # will basically show on the browser the uploaded file
        if user_id:
            db.update (
                "users", {
                    "id": user_id,
                    "avatar": filename
                }
            )
        elif project_id:
            db.insert (
                "image",
                image = filename,
                project_id = project_id
            )
        return redirect('/')

# Route that will process the file upload to a folder and
# will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be show after the upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
        filename)

# Route that will load the uploaded image to user profile
@app.route('/profile/upload', methods=['POST'])
def profile_upload():
    return redirect('/all_students'
        )

@app.route("/new_project")
def new_project():
    query_skills = db.query("""
        select
        	skill.id,
        	name
        from
        	skill;
        """)
    skills_list = query_skills.namedresult()
    query_users = db.query("""
        select
        	users.id,
        	first_name,
            last_name,
            user_type.type
        from
        	users,
        	users_link_type,
        	user_type
        where
        	users_link_type.user_id = users.id and
        	users_link_type.user_type_id = user_type.id and
        	user_type.type = 'Student'
        order by
	        first_name
        ;
        """)
    users_list = query_users.namedresult()
    print "Users List: %s \n\n\n" % users_list
    return render_template (
        "add_new_project.html",
        skills = skills_list,
        developers = users_list
    )

@app.route("/add_new_project", methods=["POST"])
def add_new_project():
    project_name = request.form.get("project_name")
    web_page = request.form.get("web_page")
    project_description = request.form.get("project_description")
    skills = request.form.getlist("skill_id")
    users = request.form.getlist("user_id")
    print "\n\nInformation received: %s\n%s\n%s\n%s\n%s\n" % (project_name, web_page, project_description, skills, users)
    print "\n\nRequest Form: %s \n\n" % request.form

    insert_new_project = db.query("""
        INSERT INTO project(name, link, description)
        VALUES
            ($1, $2, $3)
        RETURNING id;
        """, (project_name, web_page, project_description))
    new_project_id = insert_new_project.namedresult()[0].id
    for skill in skills:
        db.insert(
            "project_link_skill",
            project_id = new_project_id,
            skill_id = int(skill)
        )
    for user in users:
        db.insert(
            "users_link_project",
            project_id = new_project_id,
            users_id = int(user)
        )
    return redirect("/")

# Route to handle any errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template (
        "404.html"
    )

if __name__ == "__main__":
    app.run(debug=True)
