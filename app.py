from flask import Flask, request, redirect, render_template, session, url_for
from flask_paginate import Pagination, get_page_parameter
import datetime
import math
import sqlite3

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/')
def index():
    """Отображение страницы авторизации."""
    return render_template('authorisation.html')

def get_table_subset(results, page, per_page):
    offset = (page - 1) * per_page
    table_subset = results[offset:offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=len(results), css_framework='bootstrap4')
    return table_subset, pagination

@app.route('/sign_in', methods=['POST'])
def sign_in():
    """
    Аутентификация пользователя и перенаправление на соответствующий интерфейс.
    
    Проверяет, есть ли введенные пользователем имя пользователя и пароль в базе данных.
    Если имя пользователя и пароль верны, пользователь перенаправляется на соответствующий интерфейс.
    Если имя пользователя и пароль неверны, пользователь перенаправляется на страницу авторизации с сообщением об ошибке.
    """
    conn = sqlite3.connect('bakaibank.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logbook")
    results = cursor.fetchall()

    per_page = 10  # количество записей на странице
    page = request.args.get(get_page_parameter(), type=int, default=1)
    table_subset, pagination = get_table_subset(results, page, per_page)

    if request.form['username'] == 'branch' and request.form['password'] == 'branch':
        session['username'] = 'branch'
        return render_template('branch_interface.html', table=table_subset, pagination=pagination)
    elif request.form['username'] == 'head' and request.form['password'] == 'head':
        session['username'] = 'head'
        return render_template('headquarters_interface.html', table=table_subset, pagination=pagination)
    else:
        return render_template('authorisation.html', error=True)

@app.route('/sign_out', methods=['POST'])
def sign_out():
    """Удаляет информацию о сеансе и перенаправляет на страницу авторизации."""
    session.pop('username', None)
    return redirect('/')

@app.route('/add', methods=['POST'])
def add_row():
    """
    Добавление новой строки в таблицу журнала.
    
    Добавляет новую строку в таблицу журнала и перенаправляет пользователя на страницу с обновленной таблицей журнала.
    """
    conn = sqlite3.connect('bakaibank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logbook")
    count = cursor.fetchone()[0]
    today = datetime.date.today()
    cursor.execute(f"insert into logbook (serial_number, applicant, agreement_number, amount, currency, start_date, expiration_date, curator, status) values ( {0}, '', {0}, {0}, '', '{today}', '{today}', '', '')")
    conn.commit()
    conn.close()

    # Получаем номер последней страницы таблицы журнала
    last_page = math.ceil(count / 10)

    # Перенаправляем пользователя на последнюю страницу таблицы журнала
    return redirect(url_for('success', page=last_page))

@app.route('/success')
def success():
    """Отображение страницы интерфейса филиала с обновленной таблицей журнала."""

    if session['username'] == 'branch':
        interface = 'branch_interface'
    elif session['username'] == 'head':
        interface = 'headquarters_interface'

    conn = sqlite3.connect('bakaibank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logbook")
    count = cursor.fetchone()[0]
    conn.close()

    # Обновляем количество страниц, учитывая новую запись
    per_page = 10  # количество записей на странице
    new_count = count + 1
    new_pages = int((new_count + per_page - 1) / per_page)

    # Получаем номер текущей страницы
    page = request.args.get(get_page_parameter(), type=int, default=1)

    # Проверяем, не превышает ли номер страницы количество страниц, которые теперь доступны
    if page > new_pages:
        page = new_pages

    # Передаем необходимые параметры в Pagination
    pagination = Pagination(page=page, total=new_count, per_page=per_page, css_framework='bootstrap4', record_name='table_subset')

    # Получаем срез таблицы для текущей страницы
    offset = (page - 1) * per_page
    conn = sqlite3.connect('bakaibank.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM logbook LIMIT {offset}, {per_page}")
    table_subset = cursor.fetchall()
    conn.close()

    pagination = Pagination(page=page, per_page=per_page, total=new_count, css_framework='bootstrap4')
    
    return render_template(f'{interface}.html', table=table_subset, pagination=pagination)


@app.route('/update', methods=['POST'])
def update():
    """
    Обновление строки в таблице журнала.
    Проверяет, соответствуют ли данные, введенные пользователем, формату и типу данных,
    затем обновляет выбранную строку в таблице журнала и перенаправляет пользователя на страницу с обновленной таблицей журнала.
    """
    id = request.form['id']

    # Проверяем, соответствуют ли данные, введенные пользователем, формату и типу данных
    try:
        serial_number = int(request.form['column1'])
        agreement_number = int(request.form['column3'])
        amount = int(request.form['column4'])
        currency = request.form['column5']
        start_date = datetime.datetime.strptime(request.form['column6'], '%Y-%m-%d')
        expiration_date = datetime.datetime.strptime(request.form['column7'], '%Y-%m-%d')
    except ValueError:
        return render_template('branch_interface.html', error=True)

    column1 = serial_number
    column2 = request.form['column2']
    column3 = agreement_number
    column4 = amount
    column5 = currency
    column6 = start_date
    column7 = expiration_date
    column8 = request.form['column8']
    column9 = request.form['column9']

    query = "UPDATE logbook SET serial_number=?, applicant=?, agreement_number=?, amount=?, currency=?, start_date=?, expiration_date=?, curator=?, status=? WHERE id=?"
    values = (column1, column2, column3, column4, column5, column6, column7, column8, column9, id)

    conn = sqlite3.connect('bakaibank.db')
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    results = cursor.fetchall()

    per_page = 10  # количество записей на странице
    page = request.args.get(get_page_parameter(), type=int, default=1)
    table_subset, pagination = get_table_subset(results, page, per_page)

    # Передаем необходимые параметры в Pagination
    return render_template('branch_interface.html', table=table_subset, pagination=pagination)




@app.route('/filter', methods=['GET'])
def filter():
    """
    Фильтрует записи в таблице журнала.
    Проверяет, соответствуют ли данные, введенные пользователем, формату и типу данных,
    затем возвращает записи, соответствующие переданным параметрам.
    """
    if session['username'] == 'branch':
        interface = 'branch_interface'
    elif session['username'] == 'head':
        interface = 'headquarters_interface'

    conn = sqlite3.connect('bakaibank.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM logbook WHERE 1=1"
    
    if request.args.get('serial_number'):
        try:
            serial_number = int(request.args.get('serial_number'))
            query += f" AND serial_number={serial_number}"
        except ValueError:
            pass
        
    if request.args.get('applicant'):
        applicant = request.args.get('applicant')
        query += f" AND applicant='{applicant}'"
        
    if request.args.get('agreement_number'):
        try:
            agreement_number = int(request.args.get('agreement_number'))
            query += f" AND agreement_number={agreement_number}"
        except ValueError:
            pass
        
    if request.args.get('amount'):
        try:
            amount = float(request.args.get('amount'))
            query += f" AND amount={amount}"
        except ValueError:
            pass
        
    if request.args.get('currency'):
        currency = request.args.get('currency')
        query += f" AND currency='{currency}'"
        
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
        query += f" AND start_date='{start_date}'"
        
    if request.args.get('expiration_date'):
        expiration_date = request.args.get('expiration_date')
        query += f" AND expiration_date='{expiration_date}'"
        
    if request.args.get('curator'):
        curator = request.args.get('curator')
        query += f" AND curator='{curator}'"
        
    if request.args.get('status'):
        status = request.args.get('status')
        query += f" AND status='{status}'"
        
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    per_page = 10  # количество записей на странице
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = (page - 1) * per_page
    table_subset = results[offset:offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=len(results), css_framework='bootstrap4')

    return render_template(f'{interface}.html', table=table_subset, pagination = pagination)

