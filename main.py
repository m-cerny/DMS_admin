# Standard imports
from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

# NiceGUI components
from nicegui import app, ui

# Local modules
from user import User, overview, clean_data
from admin import Admin
from auth import Authentification
from config import CONST

# Misc utilities
from time import sleep
import asyncio, re

"""
todo:

"""

# Paths that don't require authentication
unrestricted_page_routes = {'/login'}


# ----------------- Middleware for Access Control -----------------

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to restrict access to authenticated users only."""

    async def dispatch(self, request: Request, call_next):
        # If not authenticated and trying to access protected route
        if not app.storage.user.get('authenticated', False):
            if not request.url.path.startswith('/_nicegui') and request.url.path not in unrestricted_page_routes:
                # Redirect to login with original destination saved
                return RedirectResponse(f'/login?redirect_to={request.url.path}')
        return await call_next(request)

# Register the middleware
app.add_middleware(AuthMiddleware)


# ----------------- Header UI (appears on all pages) -----------------

def header():
    username = app.storage.user.get('username')
    actual_user = User(username)
    with ui.header(elevated=True).style('background-color: #000000').classes('items-center justify-between'):
        ui.link(CONST["HEAD"], "/").classes('text-2xl')  # Logo/Home link
        with ui.card().classes('bg-blue-500 text-white'):
            ui.label(f'You are logged as: {actual_user.name}')
            if actual_user.is_admin():
                ui.label(f'You have administrator privilege')
        with ui.column():
            ui.link('Admin', "admin")
            ui.button(on_click=Authentification.logout, icon='logout').props('outline round')


# ----------------- Main User Page -----------------
@ui.page('/')
def main_page():
    ui.element('div')
    header()
    user_data = app.storage.user.get('username')
    if user_data:
        current_user = User(user_data)

        with ui.row():

            # Statistics card
            with ui.card():
                
                    ui.label("Overview:")
                    
                    data_list = [current_user.stats]
                    #print(data_list[0]["email"])                    
                    ui.table(
                        rows=clean_data(data_list)
                        )

            # Password change card
            with ui.card():
                ui.label("Change your password:")
                new_password = ui.input('Password', password=True, password_toggle_button=True,
                                        validation={'Too short': lambda value: len(value) > 5})
                ui.button('Confirm', on_click=lambda e: current_user.setup("pswd_change", new_pswd=new_password.value), color="red")

            # Alias management card
            with ui.card():
                ui.label("Aliases management:")

                # Add alias
                with ui.card_section():
                    ui.label("Add new alias:")
                    add_alias_ = ui.input('Adress', password=False,
                                          validation={'wrong format!': lambda value: User.is_valid_email(value)})

                    async def click_handle():
                        current_user.setup("add_alias", alias=add_alias_.value)
                        await asyncio.sleep(2)
                        ui.navigate.to("/")  # Refresh page

                    ui.button('Confirm', on_click=click_handle)

                # Delete alias
                with ui.card_section():
                    aliases_list = current_user.aliases
                    #aliases_list = aliases_list[user_data]["aliases"]
                    print(aliases_list)
                    selected_alias = []

                    def selection_handle(e):
                        selected_alias.append(e.value)

                    async def click_handle_del(selected_alias):
                        current_user.setup("del_alias", alias=selected_alias[-1])
                        await asyncio.sleep(2)
                        ui.navigate.to("/")

                    ui.label("Delete alias:")
                    if aliases_list != None:
                        ui.select(aliases_list, multiple=False, on_change=selection_handle, clearable=True)
                        ui.button('Confirm', on_click=lambda e: click_handle_del(selected_alias))
                    else:
                        ui.label("No aliases")
                    

        ui.separator()
    else:
        # No user in storage? Force logout
        Authentification.logout()


# ----------------- Admin Page -----------------

@ui.page('/admin')
def admin_page():
    user_data = app.storage.user.get('username')
    if user_data:
        current_user = User(user_data)

        if current_user.is_admin():
            users = Admin.email("list")
            quota_users = Admin.quota_users(Admin.overview())
            nonquota_users = list(set(users) - set(quota_users))
            header()

            with ui.row():
                # Users overview card
                with ui.card():
                    ui.label("Overview:")
                    ui.table(
                        columns=[
                            {"name": "email", "label": "Email", "field": "email"},
                            {"name": "used", "label": "Used", "field": "used"},
                            {"name": "quota", "label": "Quota", "field": "quota"},
                            {"name": "percent_used", "label": "% Used", "field": "percent_used"},
                            {"name": "aliases", "label": "Aliases", "field": "aliases"},
                        ],
                        rows=clean_data(overview())
                        )

                # User management card
                with ui.card():
                    ui.label("User management:")

                    # Add user
                    with ui.card_section():
                        async def click_handle_add(username_, password_):
                            if User.is_valid_email(username_):
                                Admin.email("add", username_, password_)
                                await asyncio.sleep(3)
                                ui.navigate.to("/admin")
                            else:
                                ui.notify("Wrong email address!", type="negative")

                        ui.label("Add a new user:")
                        username = ui.input('Username', password=False,
                                            validation={'wrong format!': lambda value: User.is_valid_email(value)})
                        password = ui.input('Password', password=True, password_toggle_button=True).on(
                            'keydown.enter', lambda e: click_handle_add(username.value, password.value))
                        ui.button('Confirm', on_click=lambda e: click_handle_add(username.value, password.value))

                    ui.separator()

                    # Delete user
                    with ui.card_section():
                        selected_users_del = []

                        def selection_handle(e):
                            selected_users_del.append(e.value)

                        async def click_handle_del(selected_users_del):
                            Admin.email("del", address=selected_users_del)
                            await asyncio.sleep(3)
                            ui.navigate.to("/admin")

                        ui.label("Delete user:")
                        ui.select(users, multiple=False, on_change=selection_handle, clearable=True)
                        ui.button('Confirm', on_click=lambda e: click_handle_del(selected_users_del))

                # Quota management card
                with ui.card():
                    ui.label("Quotas:")

                    # Set quota
                    with ui.card_section():
                        sel_nonquota_users = []
                        def sel_handle_quota_set(e):
                            sel_nonquota_users.append(e.value)

                        async def click_handle_quota_set(sel_nonquota_users):
                            Admin.quota("set", address=sel_nonquota_users, quota=slider.value)
                            await asyncio.sleep(3)
                            ui.navigate.to("/admin")
                        ui.label("Set quota to user:")
                        with ui.card_section():
                            ui.select(nonquota_users, multiple=False, on_change=sel_handle_quota_set, clearable=True)
                        with ui.card_section():
                            with ui.row():
                                ui.label("Size (MiB):")
                                slider=ui.slider(min=100, max=5000, value=500, step=100)
                                ui.label().bind_text_from(slider, 'value')
                        ui.button('Confirm', on_click=lambda e: click_handle_quota_set(sel_nonquota_users))
                    
                    ui.separator()

                    # Delete quota
                    with ui.card_section():
                        sel_users_quota = []

                        def sel_handle_quota_del(e):
                            sel_users_quota.append(e.value)

                        async def click_handle_quota_del(sel_users_quota):
                            Admin.quota("del", address=sel_users_quota)
                            await asyncio.sleep(3)
                            ui.navigate.to("/admin")

                        ui.label("Delete user's quota:")
                        ui.select(quota_users, multiple=False, on_change=sel_handle_quota_del, clearable=True)
                        ui.button('Confirm', on_click=lambda e: click_handle_quota_del(sel_users_quota))
                        #ui.date().props('''default-year-month=2023/01 :options="date => !['2023/01/01', '2023/01/15'].includes(date)"''')


        else:
            # Non-admin trying to access admin page
            header()
            ui.label("You are not an administrator!")


# ----------------- Login Page -----------------

@ui.page('/login')
def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    """Login page with optional redirection after login."""

    def try_login(username, password):
        if Authentification.auth(username, password):
            app.storage.user.update({'username': username, 'authenticated': True})
            loged_user = User(app.storage.user.get("username"))
            ui.navigate.to(redirect_to)
        else:
            ui.notify('Wrong username or password', color='negative')

    # If already authenticated, go to home
    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')

    # Login UI
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter',
                                           lambda e: try_login(username.value, password.value))
        password = ui.input('Password', password=True, password_toggle_button=True).on(
            'keydown.enter', lambda e: try_login(username.value, password.value))
        ui.button('Log in', on_click=lambda e: try_login(username.value, password.value))

    return None


# ----------------- App Entry Point -----------------

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        storage_secret="kusudASIDPOADDAF",
        dark=None,
        port=8080,
        host="0.0.0.0",
        title=CONST["HEAD"],
        language='cs'
        
    )
