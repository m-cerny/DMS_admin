from typing import Optional

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import subprocess
from nicegui import app, ui
from passlib.hash import sha512_crypt

"""
todo:
- vytvoreni aliasu pro prihlaseneho uzivatele

    
"""
# Function to load users from a file
admins =  ("m.cerny@redandblack.cz")
head = "DMS administration"

def load_users(filename='postfix-accounts.cf'):
    users = {}
    with open(filename, 'r') as f:
        for line in f:
            username, password_hash = line.strip().split('|{SHA512-CRYPT}')
            users[username] = password_hash
    return users

# Function to load email aliases
def load_aliases(filename='postfix-virtual.cf'):
    aliases = {}
    with open(filename, 'r') as f:
        for line in f:
            alias, username = line.strip().split()
            if username in aliases:
                aliases[username].append(alias)
            else:
                aliases[username] = [alias]
    return aliases

# Function to add new alias
def add_alias():
    pass

def logout() -> None:
        app.storage.user.clear()
        ui.navigate.to('/login')

unrestricted_page_routes = {'/login'}

class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.

    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if not request.url.path.startswith('/_nicegui') and request.url.path not in unrestricted_page_routes:
                return RedirectResponse(f'/login?redirect_to={request.url.path}')
        return await call_next(request)


app.add_middleware(AuthMiddleware)

def pswd_change(new_pswd):
    if len(new_pswd) > 5:
        try:       
            #process = subprocess.run(f"docker exec -it mailserver setup email add {new_pswd}", shell=True, capture_output=True)
            process = subprocess.run("print", shell=True, capture_output=True)
            if process.returncode == 0:
                ui.notify("Password changed",color='positive')
            else:
                ui.notify("Something wrong!",color='negative')
        except:
            ui.notify("Something wrong!", color='negative')
    else:
        ui.notify("Use at least 6 characters!")

@ui.page('/')
def main_page() -> None:

    with ui.header(elevated=True).style('background-color: #000000').classes('items-center justify-between'):
        ui.label(head).classes('text-2xl') 
        with ui.column():            
            ui.link('Admin', "admin").style
            ui.button(on_click=logout, icon='logout').props('outline round')
    ui.label(f'You are logged as: {app.storage.user["username"]}')
    with ui.card(): #.classes('absolute-center items-center')
        new_password = ui.input('New Password', password=True, password_toggle_button=True, validation={'Too short': lambda value: len(value) > 5})
        ui.button('Confirm', on_click=lambda e: pswd_change(new_password.value))
    ui.separator()

            

@ui.page('/admin')
def admin_page() -> None:
    if app.storage.user["username"] in admins:
        with ui.header(elevated=True).style('background-color: #000000').classes('items-center justify-between'):
            ui.label(head).classes('text-2xl') 
            ui.button(on_click=logout, icon='logout').props('outline round')
        with ui.card():
            ui.label(f"Your aliases:")
            with ui.list():              
                try:
                    user_aliases = load_aliases()[app.storage.user["username"]]
                    for i, item in enumerate(user_aliases):
                        ui.label(user_aliases[i])
                except: ui.label("No aliases found")
        add_alias = ui.input('Add alias', password=False, validation={'Too short': lambda value: len(value) > 5})
        ui.button('Confirm', on_click=lambda e: add_alias(add_alias.value))
    else:
        with ui.header(elevated=True).style('background-color: #000000').classes('items-center justify-between'):
            ui.label("Red&Black email administration").classes('text-2xl') 
            ui.button(on_click=logout, icon='logout').props('outline round')
        ui.label("You are not administrator!")
        

@ui.page('/login')
def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    def auth(username, pswd):
        if username in load_users():
            return sha512_crypt.verify(pswd, load_users()[username])
    
    def try_login(username, password) -> None:
        if auth(username, password) == True:
            app.storage.user.update({'username': username, 'authenticated': True})
            ui.navigate.to(redirect_to)  # go back to where the user wanted to go
        else:
            ui.notify('Wrong username or password', color='negative')
    
    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')

    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter', lambda e: try_login(username.value, password.value))
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', lambda e: try_login(username.value, password.value))
        ui.button('Log in', on_click=lambda e: try_login(username.value, password.value))
    return None


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(storage_secret="kusudASIDPOADDAF", dark=True, port=8080, host= 0.0.0.0)