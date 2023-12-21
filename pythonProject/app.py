from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from passlib.hash import bcrypt

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

def verify_password(input_password, hashed_password):
    return bcrypt.verify(input_password, hashed_password)

@app.route('/', methods=['POST'])
def login_in():
    login = request.form.get('login')
    password = request.form.get('password')

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
        # Передаем данные в шаблон
        return render_template("teacher.html", user_data=user_data)
    else:
        # Если нет данных в сессии, перенаправляем на страницу входа
        return redirect(url_for('show_index_form'))

    return render_template("teacher.html")

@app.route('/student')
def show_student_form():
    if 'user_data' in session:
        # Получаем данные пользователя из сессии
        user_data = session['user_data']
        # Передаем данные в шаблон
        return render_template("student.html", user_data=user_data)
    else:
        # Если нет данных в сессии, перенаправляем на страницу входа
        return redirect(url_for('show_index_form'))

    return render_template("student.html")
@app.route('/logout')
def logout():
    session.clear()
    print("сессия завершена")
    return redirect(url_for('show_index_form'))

if __name__ == "__main__":
    app.run(debug=True)