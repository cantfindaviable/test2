import streamlit as st
import requests
import time
from typing import Optional, List, Dict
import pandas as pd
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Конфигурация
FASTAPI_URL = "http://app:8080"

# Базовые классы
class Page(ABC):
    """Абстрактный класс страницы"""
    def __init__(self, app: 'App'):
        self.app = app
    
    @abstractmethod
    def render(self):
        pass

    def navigate_to(self, page_name: str):
        self.app.current_page = page_name
        st.session_state.current_page = page_name
        time.sleep(0.3)  
        st.rerun()

@dataclass
class UserData:
    token: Optional[str] = None
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    
    def is_authenticated(self) -> bool:
        return self.token is not None

class AuthManager:
    """Исправленный класс AuthManager с конструктором"""
    def __init__(self, app: 'App'):  # Добавлен конструктор
        self.app = app
    
    # @property
    # def is_authenticated(self):
    #     return st.session_state.user_data.token is not None
    
    def login(self, email: str, password: str) -> bool:
        try:
            response = requests.post(...)
            response.raise_for_status()
            
            token = response.json().get("access_token")
            user_info = self._get_user_info(token)
            
            if user_info:
                st.session_state.update({
                    'user_data': UserData(
                        token=token,
                        user_id=user_info["id"],
                        user_email=user_info["email"]
                    ),
                    'current_page': 'dashboard'  
                })
                st.success('Авторизация успешна!')
                time.sleep(0.5)  
                st.rerun()  
                return True
                
        except Exception as e:
            st.error(f"Ошибка авторизации: {str(e)}")
        return False
    
    def signup(self, email: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{FASTAPI_URL}/api/users/signup",
                json={"email": email, "password": password}
            )
            response.raise_for_status()
            
            token = response.json().get("access_token")
            user_info = self._get_user_info(token)
            
            if user_info:
                # Обновляем оба места хранения состояния
                st.session_state.user_data = UserData(
                    token=token,
                    user_id=user_info["id"],
                    user_email=user_info["email"]
                )
                self.app.user_data = st.session_state.user_data  # Синхронизируем
                
                st.success("Регистрация успешна!")
                time.sleep(0.5)
                self.app.current_page = 'dashboard'
                st.session_state.current_page = 'dashboard'
                st.rerun()
                return True
                
        except Exception as e:
            st.error(f"Ошибка регистрации: {str(e)}")
        return False
        
    def logout(self):
        st.session_state.user_data = UserData()
        self.app.user_data = st.session_state.user_data
        st.success("Вы вышли из системы")
        time.sleep(0.5)
        self.app.current_page = 'home'
        st.session_state.current_page = 'home'
        st.rerun()
    
    def _get_user_info(self, token: str) -> Optional[Dict]:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{FASTAPI_URL}/api/users/me", 
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except:
            return None

class TaskManager:
    """Менеджер задач с обработкой ошибок"""
    def __init__(self, app: 'App'):
        self.app = app
    
    def create_task(self, message: str, brandbook_id: Optional[str] = None) -> Optional[int]:
        try:
            headers = {"Authorization": f"Bearer {self.app.user_data.token}"}
            data = {"message": message}
            if brandbook_id:
                data["brandbook_id"] = brandbook_id
                
            response = requests.post(
                f"{FASTAPI_URL}/api/ml/send_task",
                data=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json().get("task_id")
            
        except Exception as e:
            st.error(f"Ошибка создания задачи: {str(e)}")
            return None
    
    def get_task_status(self, task_id: int) -> Optional[Dict]:
        try:
            response = requests.get(f"{FASTAPI_URL}/api/ml/tasks/{task_id}")
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def get_user_tasks(self) -> List[Dict]:
        if not self.app.user_data.user_id:
            return []
            
        try:
            response = requests.get(
                f"{FASTAPI_URL}/api/ml/tasks/user/{self.app.user_data.user_id}"
            )
            response.raise_for_status()
            return response.json()
        except:
            return []

# Страницы приложения
class HomePage(Page):
    def render(self):
        st.title("Генератор изображений по брендбуку")
        st.markdown("""
        ### Создавайте изображения, соответствующие вашему брендбуку
        
        **Возможности сервиса:**
        - Загрузка брендбука
        - Генерация изображений по текстовому описанию
        - Просмотр истории задач
        - Анализ соответствия брендбуку
        """)
        
        if st.button("Начать работу", type="primary"):
            self.navigate_to("auth")

class AuthPage(Page):
    def render(self):
        st.title("🔐 Авторизация")
        
        tab_login, tab_signup = st.tabs(["Вход", "Регистрация"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Пароль", type="password", key="login_pwd")
                if st.form_submit_button("Войти", type="primary"):
                    if self.app.auth.login(email, password):
                        self.navigate_to("dashboard")
        
        with tab_signup:
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                password = st.text_input("Пароль", type="password", key="signup_pwd")
                if st.form_submit_button("Зарегистрироваться", type="primary"):
                    if self.app.auth.signup(email, password):
                        self.navigate_to("dashboard")
        
        if st.button("На главную"):
            self.navigate_to("home")
class BrandbookPage(Page):
    def render(self):
        if not st.session_state.user_data.is_authenticated():
            self.navigate_to("auth")
            return
            
        st.title("Управление брендбуками")
        
        tab1, tab2 = st.tabs(["Загрузить новый брендбук", "Мои брендбуки"])
        
        with tab1:
            self._render_upload_form()
        
        with tab2:
            self._render_brandbooks_list()
        
        if st.button("← Назад"):
            self.navigate_to("dashboard")
    
    def _render_upload_form(self):
        with st.form("upload_form"):
            st.subheader("Загрузить новый брендбук")
            
            name = st.text_input("Название брендбука*", help="Например: Альфа-Банк 2023")
            description = st.text_area("Описание")
            file = st.file_uploader(
                "Файл брендбука (PDF)*", 
                type=["pdf"],
                accept_multiple_files=False
            )
            
            if st.form_submit_button("Загрузить", type="primary"):
                if not name or not file:
                    st.error("Пожалуйста, заполните все обязательные поля (помечены *)")
                else:
                    self._upload_brandbook(name, description, file)
    
    def _upload_brandbook(self, name: str, description: str, file):
        with st.spinner("Загружаем брендбук..."):
            try:
                headers = {"Authorization": f"Bearer {self.app.user_data.token}"}
                
                files = {
                    "file": (file.name, file.getvalue(), "application/pdf")
                }
                data = {
                    "name": name,
                    "description": description or ""
                }
                
                response = requests.post(
                    f"{FASTAPI_URL}/api/brandbooks/upload",
                    files=files,
                    data=data,
                    headers=headers
                )
                response.raise_for_status()
                
                st.success("Брендбук успешно загружен!")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Ошибка загрузки: {str(e)}")
    
    def _render_brandbooks_list(self):
        try:
            headers = {"Authorization": f"Bearer {self.app.user_data.token}"}
            response = requests.get(
                f"{FASTAPI_URL}/api/brandbooks",
                headers=headers
            )
            response.raise_for_status()
            brandbooks = response.json()
            
            if not brandbooks:
                st.info("У вас пока нет загруженных брендбуков")
                return
                
            for book in brandbooks:
                with st.expander(f"📖 {book.get('name', 'Без названия')}"):
                    cols = st.columns([1, 3])
                    with cols[0]:
                        st.metric("Статус", book.get("status", "unknown").upper())
                        if st.button(
                            "Удалить", 
                            key=f"delete_{book['id']}",
                            type="secondary"
                        ):
                            self._delete_brandbook(book["id"])
                    
                    with cols[1]:
                        st.write(f"**Описание:** {book.get('description', 'Нет описания')}")
                        st.write(f"**Загружен:** {book.get('created_at', '')}")
                        st.download_button(
                            "Скачать PDF",
                            data=requests.get(
                                f"{FASTAPI_URL}/api/brandbooks/{book['id']}/download",
                                headers=headers
                            ).content,
                            file_name=f"{book['name']}.pdf",
                            mime="application/pdf"
                        )
                        
        except Exception as e:
            st.error(f"Ошибка получения списка брендбуков: {str(e)}")
    
    def _delete_brandbook(self, book_id: int):
        try:
            headers = {"Authorization": f"Bearer {self.app.user_data.token}"}
            response = requests.delete(
                f"{FASTAPI_URL}/api/brandbooks/{book_id}",
                headers=headers
            )
            response.raise_for_status()
            st.success("Брендбук успешно удален")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка удаления: {str(e)}")

class DashboardPage(Page):
    
    def render(self):
        if not hasattr(st.session_state, 'user_data') or not st.session_state.user_data.is_authenticated():
            st.session_state.current_page = 'auth'
            st.error("Требуется авторизация")
            time.sleep(1)
            st.rerun()
            return
        
        st.title(f"Привет, {st.session_state.user_data.user_email}!")
            
        cols = st.columns(3)
        with cols[0]:
            if st.button("Новая задача", use_container_width=True):
                self.navigate_to("create_task")
        with cols[1]:
            if st.button("История задач", use_container_width=True):
                self.navigate_to("history")
        with cols[2]:
            if st.button("Загрузить брендбук", use_container_width=True):
                self.navigate_to("brandbooks")
        
        if st.button("Выйти", type="secondary"):
            self.app.auth.logout()
            self.navigate_to("home")

class CreateTaskPage(Page):
    def render(self):
        if not st.session_state.user_data.is_authenticated():
            self.navigate_to("auth")
            return
            
        st.title("Создание задачи")
        
        BRANDBOOKS = {
            "Большой театр": "brandbook__1_pdf",
            "X5 Group": "brandbook__2_pdf",
            "Альфа-Банк": "brandbook__3_pdf"
        }
        
        with st.form("task_form"):
            brandbook = st.selectbox(
                "Выберите брендбук",
                options=list(BRANDBOOKS.keys()),
                format_func=lambda x: x
            )
            
            prompt = st.text_area(
                "Опишите желаемое изображение",
                placeholder="Например: логотип для IT компании в синих тонах..."
            )
            
            submitted = st.form_submit_button("Создать задачу", type="primary")
            
            if submitted and prompt:
                with st.spinner("Создание задачи..."):
                    task_id = self.app.tasks.create_task(
                        prompt, 
                        BRANDBOOKS[brandbook]
                    )
                    
                    if task_id:
                        self._monitor_task(task_id)
        
        if st.button("← Назад"):
            self.navigate_to("dashboard")
    
    def _monitor_task(self, task_id: int):
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        result_placeholder = st.empty()
        
        max_attempts = 130
        attempt = 0
        task_completed = False
        
        while attempt < max_attempts and not task_completed:
            attempt += 1
            progress = min(100, attempt * (100 // max_attempts))
            progress_bar.progress(progress)
            
            try:
                task = self.app.tasks.get_task_status(task_id)
                
                if not task:
                    status_placeholder.warning("Ожидаем ответ от сервера...")
                    time.sleep(3)
                    continue
                    
                status = task.get("status", "").lower() 
                
                if status == "completed":
                    progress_bar.progress(100)
                    result_placeholder.success("Задача успешно выполнена!")
                    
                    image_url = task.get("image_url", "")
                    if image_url:
                        try:
                            st.image(image_url, caption="Результат", width=400)
                        except:
                            try:
                                st.image(f"/app/{image_url}", caption="Результат", width=400)
                            except:
                                st.warning("Не удалось загрузить изображение")
                    
                    if enhanced_prompt := task.get("enhanced_prompt"):
                        with st.expander("Улучшенный промпт"):
                            st.write(enhanced_prompt)

                    if context := task.get("context"):
                        with st.expander("Найденный контекст"):
                            st.write(context)
                    
                    task_completed = True
                    return  # Явный выход при успешном завершении
                    
                elif status == "failed":
                    progress_bar.progress(100)
                    result_placeholder.error(f"Ошибка: {task.get('error', 'Неизвестная ошибка')}")
                    task_completed = True
                    return
                    
                # Обновляем статус
                status_text = f"""
                **Статус задачи:** {status.upper()}
                **Попытка:** {attempt}/{max_attempts}
                """
                status_placeholder.markdown(status_text)
                
                # Гибкие интервалы проверки
                delay = {
                    "queued": 5,
                    "processing": 3,
                    "started": 2
                }.get(status, 2)
                
                time.sleep(delay)
                
            except Exception as e:
                status_placeholder.error(f"Ошибка соединения: {str(e)}")
                time.sleep(5)
        
        if not task_completed:
            progress_bar.progress(100)
            result_placeholder.error("Превышено время ожидания ответа от сервера")

class HistoryPage(Page):
    def render(self):
        if not st.session_state.user_data.is_authenticated():
            self.navigate_to("auth")
            return
            
        st.title("История задач")
        
        tasks = self.app.tasks.get_user_tasks()
        
        if not tasks:
            st.info("Нет выполненных задач")
            if st.button("← Назад"):
                self.navigate_to("dashboard")
            return
        
        df = pd.DataFrame([
            {
                "ID": t["id"],
                "Статус": t.get("status", "").upper(),
                "Запрос": t.get("question", ""),
                "Дата": t.get("created_at", ""),
                "Брендбук": t.get("brandbook_id", "")
            }
            for t in tasks
        ])
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn(width="small"),
                "Статус": st.column_config.TextColumn(width="small")
            }
        )
        
        selected_id = st.selectbox(
            "Выберите задачу для просмотра",
            options=df["ID"].tolist(),
            format_func=lambda x: f"Задача #{x}"
        )
        
        selected_task = next(t for t in tasks if t["id"] == selected_id)
        if selected_task:
            self._display_task_details(selected_task)
        
        if st.button("← Назад"):
            self.navigate_to("dashboard")
    
    def _display_task_details(self, task: Dict):
        st.divider()
        st.subheader(f"Детали задачи #{task['id']}")
        
        cols = st.columns(2)
        with cols[0]:
            st.metric("Статус", task.get("status", "").upper())
            if image_url := task.get("image_url"):
                st.image(f'/app/{image_url}', width=400)
        with cols[1]:
            st.metric("Брендбук", task.get("brandbook_id", "Не указан"))
            enhanced_prompt = task.get("enhanced_prompt")
            if enhanced_prompt:
                with st.expander("Улучшенный промпт"):
                    st.write(enhanced_prompt)

            context = task.get("context")
            if context:
                with st.expander("Найденный контекст"):
                    st.write(context)

# Основное приложение
class App:
    def __init__(self):
        # Инициализация
        if 'user_data' not in st.session_state:
            st.session_state.user_data = UserData()
        
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'
        
        self.user_data = st.session_state.user_data
        self.current_page = st.session_state.current_page
        
        self.auth = AuthManager(self)
        self.tasks = TaskManager(self)
        
        self.pages = {
            'home': HomePage(self),
            'auth': AuthPage(self),
            'dashboard': DashboardPage(self),
            'create_task': CreateTaskPage(self),
            'history': HistoryPage(self),
            'brandbooks': BrandbookPage(self),
        }
    
    def run(self):
        page = self.pages.get(st.session_state.current_page, self.pages['home'])
        page.render()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Генератор изображений"
    )
    
    app = App()
    app.run()