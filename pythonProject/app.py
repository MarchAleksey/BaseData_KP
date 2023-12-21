from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from passlib.hash import bcrypt
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key'
def connect_to_db():
    try:
        connection = psycopg2.connect(
            host = 'localhost',
            database = 'bd',
            user = 'admin',
            password = 'root',
            port = '5433'
        )
        print("Успешное подключение к базе данных")
        return connection
    except (Exception, psycopg2.DatabaseError) as error:
        print("Ошибка при подключении к базе данных", error)
        return None

#Маршрут для отображения формы регистрации
@app.route('/registration', methods=['GET'])
def show_registration_form():
    return render_template("registration.html")

# Маршрут для обработки данных из формы регистрации
@app.route('/registration', methods=['POST'])
def process_registration_form():
    # Получаем данные из формы
    name = request.form.get('username')
    surname = request.form.get('surname')
    sex = request.form.get('sex')
    passport_number = request.form.get('passport_number')
    status = request.form.get('status')
    login = request.form.get('login')
    password = request.form.get('password')

    # Подключаемся к базе данных
    connection = connect_to_db()
    if connection:
        try:
            # Используем контекстный менеджер для управления курсором
            with connection.cursor() as cursor:
                # Ваш SQL-запрос для вставки данных в базу данных
                hashed_password = bcrypt.hash(password)
                sql_query = "INSERT INTO person (name, surname, sex, password, login, passport_number) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_person;"
                cursor.execute(sql_query, (name, surname, sex, hashed_password, login, passport_number))
                id_person = cursor.fetchone()[0]

                if status == 'student':
                    id_group = 1

                    sql_query_student = "INSERT INTO student (id_person, id_group) VALUES (%s, %s);"
                    cursor.execute(sql_query_student, (id_person, id_group))

                if status == 'teacher':
                    id_department = 1

                    sql_query_student = "INSERT INTO teacher(id_person, id_department) VALUES (%s, %s);"
                    cursor.execute(sql_query_student, (id_person, id_department))

                connection.commit()
            print("Данные успешно записаны в базу данных")
        except Exception as error:
            print("Ошибка при записи данных в базу данных", error)
        finally:
            connection.close()
    return redirect(url_for('show_registration_form'))

def get_user_data(login):
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql_query = "SELECT * FROM person WHERE login = %s;"
                cursor.execute(sql_query, (login,))
                user_data = cursor.fetchone()
                if user_data:
                    user_data = {
                        'id': user_data[0],
                        'name': user_data[1],
                        'surname': user_data[2],
                        'sex': user_data[3],
                        'password': user_data[4],
                        'login': user_data[5],
                        'passport_number': user_data[6],
                    }

                return user_data
        except Exception as error:
            print("Ошибка при получении данных пользователя", error)
        finally:
            connection.close()
    return None

def get_user_role(login):
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql_query = """
                    SELECT
                        CASE
                            WHEN teacher.id_teacher IS NOT NULL THEN 'teacher'
                            WHEN student.id_student IS NOT NULL THEN 'student'
                            ELSE 'Неизвестно'
                        END AS role
                    FROM
                        person
                    LEFT JOIN
                        teacher ON person.id_person = teacher.id_person
                    LEFT JOIN
                        student ON person.id_person = student.id_person
                    WHERE
                        person.login = %s;
                """
                cursor.execute(sql_query, (login,))
                result = cursor.fetchone()

                if result:
                    return result[0]
        except Exception as error:
            print("Ошибка при получении роли пользователя", error)
        finally:
            connection.close()
    return 'Неизвестно'

def get_student_group_info(login):
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql_query = """
                    SELECT
                        person.login AS student_login,
                        "group"."name" AS group_name,
                        "group".course_number AS course_number
                    FROM
                        person
                    JOIN
                        student ON person.id_person = student.id_person
                    JOIN
                        "group" ON student.id_group = "group".id_group
                    WHERE
                        person.login = %s;
                """
                cursor.execute(sql_query, (login,))
                student_group_info = cursor.fetchone()

                if student_group_info:
                    return {
                        'student_login': student_group_info[0],
                        'group_name': student_group_info[1],
                        'course_number': student_group_info[2],
                    }
        except Exception as error:
            print("Ошибка при получении данных о группе студента", error)
        finally:
            connection.close()
    return None

def get_teacher_department_info(login):
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql_query = """
                    SELECT
                        department.name AS department_name,
                        department.adress AS department_adress
                    FROM
                        teacher
                    JOIN
                        department ON teacher.id_department = department.id_department
                    JOIN
                        person ON teacher.id_person = person.id_person
                    WHERE
                        person.login = %s;
                """
                cursor.execute(sql_query, (login,))
                teacher_department_info = cursor.fetchone()

                if teacher_department_info:
                    return {
                        'department_name': teacher_department_info[0],
                        'department_adress': teacher_department_info[1],
                    }
        except Exception as error:
            print("Ошибка при получении данных о департаменте преподавателя", error)
        finally:
            connection.close()
    return None

def get_student_marks(login):
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql_query = """
                    SELECT
                        subject.name AS subject_name,
                        mark.value AS value,
                        mark.date AS date
                    FROM
                        person
                    JOIN
                        student ON person.id_person = student.id_person
                    JOIN
                        mark ON student.id_student = mark.id_student
                    JOIN
                        subject ON mark.id_subject = subject.id_subject
                    WHERE
                        person.login = %s;
                """
                cursor.execute(sql_query, (login,))
                student_marks = cursor.fetchall()

                if student_marks:
                    return [{'subject_name': mark[0], 'value': mark[1], 'date': mark[2]} for mark in student_marks]
        except Exception as error:
            print("Ошибка при получении оценок студента", error)
        finally:
            connection.close()
    return []
@app.route('/teacher/change_marks', methods=['POST'])

@app.route('/teacher/change_marks', methods=['POST'])
def change_student_marks():
    if 'user_data' in session:
        # Получаем данные пользователя из сессии
        user_data = session['user_data']
        login = user_data['login']

        # Проверяем, что пользователь - учитель
        if get_user_role(login) == 'teacher':
            # Получаем данные из формы
            student_name = request.form.get('student_name')
            student_surname = request.form.get('student_surname')
            group_name = request.form.get('group_name')
            subject_name = request.form.get('subject_name')
            new_value = request.form.get('new_value')

            connection = connect_to_db()
            if connection:
                try:
                    with connection.cursor() as cursor:
                        # Получаем id студента, id предмета и id учителя
                        sql_student_id = """
                            SELECT student.id_student
                            FROM person
                            JOIN student ON person.id_person = student.id_person
                            JOIN "group" ON student.id_group = "group".id_group
                            WHERE person.name = %s AND person.surname = %s AND "group"."name" = %s;
                        """
                        cursor.execute(sql_student_id, (student_name, student_surname, group_name))
                        student_id = cursor.fetchone()[0]

                        sql_subject_id = "SELECT id_subject FROM subject WHERE name = %s;"
                        cursor.execute(sql_subject_id, (subject_name,))
                        subject_id = cursor.fetchone()[0]

                        sql_teacher_id = "SELECT id_teacher FROM teacher WHERE id_person = (SELECT id_person FROM person WHERE login = %s);"
                        cursor.execute(sql_teacher_id, (login,))
                        teacher_id = cursor.fetchone()[0]

                        # Проверяем, что учитель ведет предмет, для которого изменяются оценки
                        sql_check_teacher_subject = "SELECT id_subject FROM subject WHERE id_teacher = %s;"
                        cursor.execute(sql_check_teacher_subject, (teacher_id,))
                        teacher_subjects = cursor.fetchall()
                        teacher_subject_ids = [subj[0] for subj in teacher_subjects]

                        if subject_id in teacher_subject_ids:
                            # Обновляем оценку
                            sql_update_mark = "UPDATE mark SET value = %s WHERE id_student = %s AND id_subject = %s;"
                            cursor.execute(sql_update_mark, (new_value, student_id, subject_id))

                            connection.commit()
                            return jsonify(success=True, message="Оценка успешно изменена")
                        else:
                            return jsonify(success=False, message="Учитель не ведет предмет с таким названием")
                except Exception as error:
                    print("Ошибка при изменении оценки", error)
                finally:
                    connection.close()

    return jsonify(success=False, message="Не удалось изменить оценку")

# Обработчик запроса на изменение группы студента
@app.route('/admin/change_student_group', methods=['POST'])
def change_student_group():
    student_login = request.form.get('student_login')
    new_group = request.form.get('new_group')

    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql_query = """
                    UPDATE student
                    SET id_group = (SELECT id_group FROM "group" WHERE "name" = %s)
                    WHERE id_person = (SELECT id_person FROM person WHERE login = %s);
                """
                cursor.execute(sql_query, (new_group, student_login))
                connection.commit()

                return jsonify(success=True, message="Группа студента успешно изменена")
        except Exception as error:
            print("Ошибка при изменении группы студента", error)
        finally:
            connection.close()
    return jsonify(success=False, message="Не удалось изменить группу студента")

# Обработчик запроса на изменение департамента преподавателя
@app.route('/admin/change_teacher_department', methods=['POST'])
def change_teacher_department():
    teacher_login = request.form.get('teacher_login')
    new_department = request.form.get('new_department')

    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor() as cursor:
                sql_query = """
                    UPDATE teacher
                    SET id_department = (SELECT id_department FROM department WHERE "name" = %s)
                    WHERE id_person = (SELECT id_person FROM person WHERE login = %s);
                """
                cursor.execute(sql_query, (new_department, teacher_login))
                connection.commit()

                return jsonify(success=True, message="Департамент преподавателя успешно изменен")
        except Exception as error:
            print("Ошибка при изменении департамента преподавателя", error)
        finally:
            connection.close()

    return jsonify(success=False, message="Не удалось изменить департамент преподавателя")

def verify_password(input_password, hashed_password):
    return bcrypt.verify(input_password, hashed_password)

@app.route('/', methods=['POST'])
def login_in():
    login = request.form.get('login')
    password = request.form.get('password')

    if login == 'admin' and password == 'admin':
        # Перенаправляем на страницу администратора
        return redirect(url_for('show_admin_form'))

    user_data = get_user_data(login)

    if user_data and verify_password(password, user_data['password']):
        # Успешная аутентификация, сохраняем данные в сессии
        session['user_data'] = user_data
        role = get_user_role(login)
        if role == 'student':
            return redirect(url_for('show_student_form'))
        elif role == 'teacher':
            return redirect(url_for('show_teacher_form'))
        else:
            # Обработка неизвестной роли (если это необходимо)
            return redirect(url_for('show_index_form'))
    else:
        # Неудачная аутентификация, возвращаем на страницу входа
        return redirect(url_for('show_index_form'))

@app.route('/')
@app.route('/home')
def show_index_form():
    return render_template("index.html")

@app.route('/teacher')
def show_teacher_form():
    if 'user_data' in session:
        # Получаем данные пользователя из сессии
        user_data = session['user_data']
        teacher_department_info = get_teacher_department_info(user_data['login'])
        # Передаем данные в шаблон
        return render_template("teacher.html", user_data=user_data, teacher_department_info=teacher_department_info)
    else:
        # Если нет данных в сессии, перенаправляем на страницу входа
        return redirect(url_for('show_index_form'))

    return render_template("teacher.html")

@app.route('/student')
def show_student_form():
    if 'user_data' in session:
        # Получаем данные пользователя из сессии
        user_data = session['user_data']
        student_group_info = get_student_group_info(user_data['login'])
        student_marks = get_student_marks(user_data['login'])
        # Передаем данные в шаблон
        return render_template("student.html", user_data=user_data, student_group_info=student_group_info, student_marks=student_marks)
    else:
        # Если нет данных в сессии, перенаправляем на страницу входа
        return redirect(url_for('show_index_form'))

    return render_template("student.html")

@app.route('/admin')
def show_admin_form():
    return render_template("admin.html")
@app.route('/logout')
def logout():
    session.clear()
    print("сессия завершена")
    return redirect(url_for('show_index_form'))

if __name__ == "__main__":
    app.run(debug=True)