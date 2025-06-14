import streamlit as st
import requests
import time
from typing import Optional, List, Dict

# Конфигурация
FASTAPI_URL = "http://app:8080"
COOKIE_NAME = "access_token"

# === Сессия пользователя ===
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "token" not in st.session_state:
    st.session_state["token"] = None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# === Авторизация ===
def login(email: str, password: str) -> bool:
    response = requests.post(
        f"{FASTAPI_URL}/auth/token",
        data={"username": email, "password": password}
    )
    data = response.json()
    if response.status_code == 200:
        # добавить ? user_info = get_current_user(token)
        # if user_info:
        #     st.session_state["token"] = token
        #     st.session_state["logged_in"] = True
        #     st.session_state["user_id"] = user_info["id"]
        #     st.success("Регистрация успешна!")
        # return True
        st.session_state["token"] = data.get("access_token")
        st.write('Вы успешно авторизировались!')
        return True
    else:
        st.error(data.get('detail'))
        return False

def signup(email: str, password: str) -> bool:
    response = requests.post(
        f"{FASTAPI_URL}/api/users/signup",
        json={"email": email, "password": password}
    )

    if response.status_code == 201:
        data = response.json()
        token = data.get("access_token")  

        user_info = get_current_user(token)
        if user_info:
            st.session_state["token"] = token
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user_info["id"]
            st.success("Регистрация успешна!")
        return True
    else:
        try:
            error_data = response.json()
            st.error(error_data.get("detail", "Ошибка регистрации"))
        except:
            st.error("Ошибка регистрации1")
        return False
    
def get_current_user(token: str) -> Optional[Dict]:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{FASTAPI_URL}/api/users/me", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error("Не удалось получить данные пользователя")
        return None
    
def get_user_tasks(user_id: int) -> List[Dict]:
    response = requests.get(f"{FASTAPI_URL}/api/ml/tasks/user/{user_id}")
    if response.status_code == 200:
        return response.json()

# === ML Задачи ===
def send_ml_task(message: str, user_id: int) -> Optional[int]:
    response = requests.post(
        f"{FASTAPI_URL}/api/ml/send_task",
        json={"message": message, "user_id": user_id}
    )
    if response.status_code == 200:
        return response.json().get("task_id")
    else:
        st.write(response.json())
        st.error("Ошибка отправки задачи")
        return None

def get_task_status(task_id: int) -> Optional[Dict]:
    response = requests.get(f"{FASTAPI_URL}/api/ml/tasks/{task_id}")
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Задача не найдена")
        return None

# === Страницы ===
def home_page():
    st.title("🖼️ Сервис генерации изображений")
    st.markdown("""
    ### Описание
    Этот сервис позволяет создавать изображения на основе текстовых запросов.
    
    #### Возможности:
    - Генерация изображений по тексту
    - Отслеживание статуса задачи
    - История всех выполненных задач
    
    Войдите или зарегистрируйтесь, чтобы начать!
    """)
    if st.button("Войти / Зарегистрироваться"):
        st.session_state["page"] = "auth"

def auth_page():
    st.title("🔐 Вход / Регистрация")
    tab1, tab2 = st.tabs(["Вход", "Регистрация"])

    with tab1:
        email_login = st.text_input("Email", key="login_email")
        password_login = st.text_input("Пароль", type="password", key="login_password")
        if st.button("Войти"):
            if login(email_login, password_login):
                st.session_state["page"] = "dashboard"
                st.rerun()

    with tab2:
        email_signup = st.text_input("Email", key="signup_email")
        password_signup = st.text_input("Пароль", type="password", key="signup_password")
        if st.button("Зарегистрироваться"):
            if signup(email_signup, password_signup):
                if login(email_signup, password_signup):
                    st.session_state["page"] = "dashboard"
                    st.rerun()

def dashboard_page():
    st.title("🚀 Личный кабинет")
    st.write(f"Привет, {st.session_state['user_id']}!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Создать новую задачу"):
            st.session_state["page"] = "create_task"
            st.rerun()
    with col2:
        if st.button("История задач"):
            st.session_state["page"] = "history"
            st.rerun()

    if st.button("Выйти"):
        st.session_state["token"] = None
        st.session_state["logged_in"] = False
        st.session_state["user_id"] = None
        st.session_state["page"] = "home"
        st.rerun()

def create_task_page():
    st.title("🆕 Создание задачи")
    prompt = st.text_area("Введите запрос для генерации изображения")

    if st.button("Отправить задачу"):
        task_id = send_ml_task(prompt, st.session_state["user_id"])
        if task_id:
            st.info(f"Задача отправлена! ID: {task_id}")
            placeholder = st.empty()

            while True:
                task = get_task_status(task_id)
                if task is None:
                    break
                status = task.get("status")
                result = task.get("result")

                with placeholder.container():
                    st.markdown(f"### Статус: `{status.upper()}`")
                    if status == "completed":
                        st.image(result, caption="Сгенерированное изображение", use_column_width=True)
                        break
                    elif status == "failed":
                        st.error("Ошибка при генерации изображения")
                        break
                    time.sleep(2)

    if st.button("Назад"):
        st.session_state["page"] = "dashboard"
        st.rerun()

def history_page():
    st.title("📜 История задач")
    tasks = get_user_tasks(st.session_state["user_id"])
    if tasks:
        for task in tasks:
            st.markdown(f"#### ID: {task['id']}")
            st.markdown(f"**Статус:** `{task['status'].upper()}`")
            if task["result"]:
                st.image(task["result"], caption="Результат", use_column_width=True)
            st.markdown("---")
    else:
        st.info("У вас пока нет задач.")

    if st.button("Назад"):
        st.session_state["page"] = "dashboard"
        st.rerun()

# === Main Loop ===
def main():
    page_router = {
        "home": home_page,
        "auth": auth_page,
        "dashboard": dashboard_page,
        "create_task": create_task_page,
        "history": history_page,
    }

    page_router.get(st.session_state["page"], home_page)()

if __name__ == "__main__":
    main()