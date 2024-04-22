import json
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


from flask import Flask, flash, render_template, request, redirect, url_for, session, g
from flask_sqlalchemy import SQLAlchemy
import requests
import bcrypt
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from emailing import sending


app = Flask(__name__)
app.config['SECRET_KEY'] = 'YOUR SECRET KEY'

db = SQLAlchemy()
db_name = "database.db"
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_name}"
db.init_app(app)

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "accept-language": "pt,en-US;q=0.9,en;q=0.8,pt-BR;q=0.7",
    "sec-ch-ua-platform": "Linux",
    "accept-Encoding": "gzip, deflate, br"
}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    email = db.Column(db.String(25))
    password = db.Column(db.String(25))


class FULLS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_name = db.Column(db.String(300))
    amazon_link = db.Column(db.String(500))
    amazon_price = db.Column(db.Integer)
    flipkart_price = db.Column(db.Integer)
    flipkart_link = db.Column(db.String(500))
    jiomart_price = db.Column(db.Integer)
    jiomart_link = db.Column(db.String(500))
    ur_limit = db.Column(db.Integer)
    status = db.Column(db.String(100))


class Ajiofull(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    p_url = db.Column(db.String(300))
    p_art = db.Column(db.Integer)
    p_name = db.Column(db.String(300))
    p_price = db.Column(db.Integer)


class Plinks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    c_link = db.Column(db.String(300))
    c_price = db.Column(db.Integer)
    from_link = db.Column(db.String(20))


with app.app_context():
    db.create_all()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.session.query(User).filter_by(email=email).first()

        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                flash("login successful", category='success')

                session['id'] = user.id
                session.modified = True
                return redirect(url_for('home'))
            else:
                flash("incorrect password", category='error')
        else:
            flash("user does not exist!!", category='error')
            return redirect('register')

    return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def sing_up():
    if request.method == 'POST':
        name_en = request.form.get('name')
        email_en = request.form.get('email')
        password_en = request.form.get('password')

        user = db.session.query(User).filter_by(email=email_en).first()

        if user:
            flash("email is already registered..", category="error")
            return redirect(url_for('login'))
        else:
            if len(password_en) < 8:
                flash("password should be greater than 8", category='error')
            else:
                pass_g = bcrypt.hashpw(password_en.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                with app.app_context():
                    new_user = User()
                    new_user.name = name_en
                    new_user.email = email_en
                    new_user.password = pass_g
                    db.session.add(new_user)
                    db.session.commit()
                user = db.session.query(User).filter_by(email=email_en).first()
                session['id'] = user.id
                return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('id', None)
    flash("logout success ful", category="success")
    return redirect(url_for('login'))


@app.before_request
def before_request():
    g.id = 0
    if 'id' in session:
        g.id = session['id']


def get_link(a, b):
    drive = Service("C:/Users/vemu/Downloads/chromedriver-win32 (2)/chromedriver-win32/chromedriver.exe")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (necessary in headless mode)

    url = "https://www.google.com"
    jsname_value = "UWckNb"
    xpath_exp = f"//a[@jsname='{jsname_value}']"

    driver = webdriver.Chrome(service=drive, options=chrome_options)
    driver.get(url=url)
    search_input = driver.find_element(By.CLASS_NAME, value="gLFyf")
    search_input.send_keys(f"{a} {b}")
    search_input.send_keys(Keys.RETURN)

    link = driver.find_element(By.XPATH, value=xpath_exp).get_attribute('href')
    return link


@app.route('/add', methods=['GET', 'POST'])
def add():
    clink = request.form.get("p_link")
    cprice = request.form.get("p_price")
    ac_link = request.form.get("link_from")
    user_id = session.get('id')
    if request.method == 'POST':
        with app.app_context():
            new_pro = Plinks()
            new_pro.user_id = user_id
            new_pro.c_link = clink
            new_pro.c_price = cprice
            new_pro.from_link = ac_link

            db.session.add(new_pro)
            db.session.commit()
        with app.app_context():
            new = FULLS()
            new.status = "pending"

            db.session.add(new)
            db.session.commit()
        last_id = db.session.query(Plinks.id).order_by(Plinks.id.desc()).first()[0]
        return redirect(url_for('load', a=last_id))
    return render_template('add.html')


@app.route("/")
def home():
    if g.id == 0:
        return redirect('login')
    else:
        return redirect(url_for('fun'))


@app.route("/load/<int:a>")
def load(a):
    return render_template("loader.html", a=a)


@app.route("/load_data/<int:a>", methods=['GET', 'POST'])
def load_data(a):
    with app.app_context():
        data = db.session.query(FULLS).filter_by(id=a).first()

        full_data = db.session.query(Plinks).filter_by(id=a).first()
        data.user_id = full_data.user_id

        link = full_data.c_link
        limit = full_data.c_price
        data.ur_limit = limit
        flag = 0
        link_of = link[12]

        def get(s_time, flag, timeout=60):
            link = data.amazon_link
            if time.time() - s_time >= timeout:
                data.amazon_price = -1
            response = requests.get(url=link, headers=headers).content
            soup = BeautifulSoup(response, "html.parser")
            price = soup.find(class_="a-price-whole")
            title = soup.find(id="productTitle")
            if price is None:
                get(start_time, timeout)

            else:
                a_price = price.text.replace(',', '')[0:]
                print(a_price)
                data.amazon_price = a_price
                if flag == 0:
                    flag = 1
                    data.product_name = title.text

        def get2(s_time, flag, timeout=60):
            link = data.flipkart_link
            if time.time() - s_time >= timeout:
                data.flipkart_price = -1
                return
            response = requests.get(url=link, headers=headers).content
            soup = BeautifulSoup(response, "html.parser")
            price = soup.find(class_="_30jeq3 _16Jk6d")
            title = soup.find(class_="B_NuCI")
            if price is None:
                get2(start_time, timeout)
            else:
                f_price = price.text.replace(',', '')[1:]
                data.flipkart_price = f_price
                if flag == 0:
                    flag = 1
                    data.product_name = title.text
                print(f_price)

        def get3(url):
            drive = Service("C:/Users/vemu/Downloads/chromedriver-win32 (2)/chromedriver-win32/chromedriver.exe")
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (necessary in headless mode)

            driver = webdriver.Chrome(service=drive, options=chrome_options)
            driver.get(url=url)
            script_input = driver.find_element(By.XPATH, value="//script[@type='application/ld+json']")
            script_content = script_input.get_attribute("innerHTML")
            if script_content and script_content.strip():  # Check if script_content exists and is not just whitespace
                mart = json.loads(script_content)
                jio_price = int(float(mart['offers']["price"]))
                data.jiomart_price = jio_price
            else:
                data.jiomart_price = -1

        if link_of == 'a':
            data.amazon_link = link
            start_time = time.time()
            get(start_time, flag)
            p_title = data.product_name
            f_link = get_link(p_title, "flipkart")
            data.flipkart_link = f_link
            start_time = time.time()
            get2(start_time, flag)
            jio_link = get_link(p_title,"jiomart")
            print(jio_link[12])
            if jio_link[12] == 'j':
                data.jiomart_link = jio_link
                get3(jio_link)
            else:
                data.jiomart_link = "no product"
                data.jiomart_price = -1
            db.session.commit()
        elif link_of == 'f':
            data.flipkart_link = link
            start_time = time.time()
            get2(start_time, flag)
            p_title = data.product_name
            a_link = get_link(p_title, "amazon")
            data.amazon_link = a_link
            start_time = time.time()
            get(start_time, flag)
            jio_link = get_link(p_title, "jiomart")
            if jio_link[12] == 'j':
                data.jiomart_link = jio_link
                get3(jio_link)
            else:
                data.jiomart_link = "no product"
                data.jiomart_price = -1
            db.session.commit()
    return redirect(url_for('view_full'))


@app.route('/test')
def fun():
    return render_template('home.html')


@app.route('/ajioload/<int:a>')
def load_ajio(a):
    return render_template("loader2.html", a=a)


@app.route("/ajio_data/<int:a>", methods=['GET', 'POST'])
def ajio_data(a):
    with app.app_context():
        details = db.session.query(Ajiofull).filter_by(id=a).first()
        key = details.p_art
        print(key)
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "accept-language": "pt,en-US;q=0.9,en;q=0.8,pt-BR;q=0.7",
            "sec-ch-ua-platform": "Linux",
            "accept-Encoding": "gzip, deflate, br"
        }
        drive = Service("C:/Users/vemu/Downloads/chromedriver-win32 (2)/chromedriver-win32/chromedriver.exe")
        chrome_options = Options()
        chrome_options.add_argument("--window-position=-2000,0")
        url = "https://www.ajio.com/"
        driver = webdriver.Chrome(service=drive, options=chrome_options)
        driver.get(url=url)
        search_input = driver.find_element(By.CSS_SELECTOR, value="input[name='searchVal")
        search_input.send_keys(f"{key}")
        search_input.send_keys(Keys.RETURN)
        details.p_url = driver.current_url
        print(driver.current_url)
        script_input = driver.find_element(By.XPATH, value="(//script[@type='application/ld+json'])[last()]")
        script_content = script_input.get_attribute("innerHTML")
        if script_content and script_content.strip():  # Check if script_content exists and is not just whitespace
            try:
                data = json.loads(script_content)
                print(data['name'])
                details.p_name = data['name']
                details.p_price = int(float(data['offers']["price"]))
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
        else:
            details.p_name = "no product"
            details.p_price = -1
        db.session.commit()
    return redirect(url_for('tends_view'))


@app.route('/ajio')
def tends_view():
    user_id = session['id']
    with app.app_context():
        full_data = Ajiofull.query.all()
    return render_template('tends_view.html', datas=full_data, user_id=user_id)


@app.route('/ajio_add',methods=['GET', 'POST'])
def tends_add():
    art_p = request.form.get("p_link")
    user_id = session.get('id')
    if request.method == 'POST':
        with app.app_context():
            new_pro = Ajiofull()
            new_pro.user_id = user_id
            new_pro.p_art = art_p
            new_pro.p_name = "no product"
            new_id = new_pro.id
            db.session.add(new_pro)
            db.session.commit()
        new_id = db.session.query(Ajiofull.id).order_by(Ajiofull.id.desc()).first()[0]
        print(new_id)
        return redirect(url_for('load_ajio', a=new_id))
    return render_template('tends_add.html')


@app.route('/view')
def view_full():
    user_id = session['id']
    with app.app_context():
        full_data = FULLS.query.all()
    return render_template('view.html', datas=full_data, user_id=user_id)


@app.route('/update')
def update():
    with app.app_context():
        full_data = FULLS.query.all()
        for data in full_data:
            if data.status == "pending":
                if data.flipkart_price != -1:
                    def get():
                        response = requests.get(url=data.flipkart_link, headers=headers).content
                        soup = BeautifulSoup(response, "html.parser")
                        price = soup.find(class_="_30jeq3 _16Jk6d")
                        if price is None:
                            get()
                        else:
                            f_price = price.text.replace(',', '')[1:]
                            data.flipkart_price = f_price
                            # print(f_price)
                    get()

                if data.amazon_price != -1:
                    def get2():
                        response = requests.get(url=data.amazon_link, headers=headers).content
                        soup = BeautifulSoup(response, "html.parser")
                        price = soup.find(class_="a-price-whole")
                        if price is None:
                            get2()
                        else:
                            a_price = price.text.replace(',', '')[0:]
                            data.amazon_price = a_price
                            # print(a_price)
                    get2()
                if data.jiomart_price != -1:
                    url = data.jiomart_link
                    drive = Service(
                        "C:/Users/vemu/Downloads/chromedriver-win32 (2)/chromedriver-win32/chromedriver.exe")
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")  # Run in headless mode
                    chrome_options.add_argument(
                        "--disable-gpu")  # Disable GPU acceleration (necessary in headless mode)

                    driver = webdriver.Chrome(service=drive, options=chrome_options)
                    driver.get(url=url)
                    script_input = driver.find_element(By.XPATH, value="//script[@type='application/ld+json']")
                    script_content = script_input.get_attribute("innerHTML")
                    if script_content and script_content.strip():  # Check if script_content exists and is not just whitespace
                        mart = json.loads(script_content)
                        jio_price = int(float(mart['offers']["price"]))
                        data.jiomart_price = jio_price
                    else:
                        data.jiomart_price = -1

        db.session.commit()
    return redirect(url_for('view_full'))


# update()


@app.route('/check')
def check():
    with app.app_context():
        full_data = FULLS.query.all()
    with app.app_context():
        users = User.query.all()
    for data in full_data:
        for user in users:
            if data.amazon_price <= data.ur_limit and data.amazon_price != -1:
                if user.id == data.user_id:
                    sending(name=f"{user.name}", receiver_email=f"{user.email}", msg=f"{data.amazon_link}")
                    print("u can buy at amazon")
            if data.flipkart_price <= data.ur_limit and data.flipkart_price != -1:
                if user.id == data.user_id:
                    sending(name=f"{user.name}", receiver_email=f"{user.email}", msg=f"{data.flipkart_link}")
                    print("u can buy at flipkart")


scheduler = BackgroundScheduler()

scheduler.add_job(check, CronTrigger(hour=10, minute=58))
scheduler.add_job(update, CronTrigger(hour=22, minute=5))


def start_scheduler():
    scheduler.start()


scheduler_thread = threading.Thread(target=start_scheduler)
scheduler_thread.start()


@app.route('/buy/<int:item_id>')
def buyed_item(item_id):
    with app.app_context():
        data_u = FULLS.query.filter_by(id=item_id).first()
        data_u.status = "product bought..."
        db.session.commit()
    return redirect(url_for('view_full'))


@app.route('/reject/<int:item_id>')
def reject_item(item_id):
    with app.app_context():
        data_u = FULLS.query.filter_by(id=item_id).first()
        data_u.status = "Email service stopped"
        db.session.commit()
    return redirect(url_for('view_full'))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
