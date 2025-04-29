import subprocess
import re
from nicegui import ui
from config import CONST

# Add to conf file
admins = CONST["ADMINS"]
container_name = CONST["CONT_NAME"]

def process(*args:str) -> dict:
    """
    keys: rc, stdout, stderr
    """
    try:
        # Running the Docker exec command
        result = subprocess.run(
            ["docker", "exec", container_name, "setup", *args], 
            check=True, 
            capture_output=True, 
            text=True  # Automatically decode stdout/stderr to string
        )

        # Prepare the output dictionary
        output = {
            "rc": result.returncode,
            "stdout": result.stdout,  # Already a string due to 'text=True'
            "stderr": result.stderr   # Capture stderr as well
        }

    except subprocess.CalledProcessError as e:
        # Handle exceptions if the command fails
        output = {
            "rc": e.returncode,
            "stdout": e.stdout if e.stdout else None,
            "stderr": e.stderr if e.stderr else None
        }

    return output

def overview():
        raw_data = process("email", "list")
        if raw_data["rc"] == 0:
            # Pattern to match email blocks
            email_block_pattern = re.compile(
                r"\* (?P<email>\S+) \(\s*(?P<used>\S+)\s*/\s*(?P<quota>\S+)\s*\) \[(?P<percent>\d+)%\](?:\s*\[\s*aliases\s*->\s*(?P<aliases>[^\]]+)\])?",
                re.MULTILINE
            )

            # Parse data
            emails_info = []

            for match in email_block_pattern.finditer(raw_data["stdout"]):
                data = match.groupdict()
                emails_info.append({
                    "email": data["email"],
                    "used": data["used"],
                    "quota": data["quota"],
                    "percent_used": int(data["percent"]),
                    "aliases": [a.strip() for a in data["aliases"].split(",")] if data["aliases"] else []
                })
            return emails_info

def clean_data(data):
    for row in data:
        row['aliases'] = ', '.join(row['aliases']) if isinstance(row['aliases'], list) else ''
        if row['quota'] == '~':
            row['quota'] = 'No quota'
    return data
        
class User:
    
    def __init__(self, name):
        self.name = name
        self.__admin = self.is_admin()
        self.aliases = self.__load_aliases()
        self.stats = self.statistics(overview())
    
    def is_admin(self):
        """Check if the user is an admin."""
        return self.name in admins

    def statistics(self, fce):
        for item in fce:
            if item["email"] == self.name:
                return item
    
    def mailbox_size(self):
        output = process("email", "list")
        if output["rc"] == 0:
            output = output["stdout"]
            print(output)

    def __load_aliases(self):
        output = process("email", "list")
        if output["rc"] == 0:
            output = output["stdout"]

            # Step 1: Clean up and split the data
            output = output.replace("\n\n", " ").strip().split("*")
            output.pop(0)

            # Step 2: Create a dictionary to store the email and its aliases
            email_alias_dict = {}

            # Step 3: Regular expression to extract the email and aliases
            for item in output:
                # Extract users email address
                email_match = re.search(r'(\S+@\S+)', item)
                if email_match:
                    email = email_match.group(1)
                    # Extract aliases
                    aliases_match = re.search(r'\[ aliases -> (.*?) \]', item)
                    if aliases_match:
                        aliases = aliases_match.group(1).split(", ")
                        # Add to dictionary
                        email_alias_dict[email] = aliases
                            
                #print(email_alias_dict)
            #return email_alias_dict[name]  
            return email_alias_dict.get(self.name)
                
    def setup (self, fc, alias=None, new_pswd=None,):

        name = self.name         

        def __alias(fc, name, alias):
            """Handle aliases."""

            if fc == "add" and name and alias:
                output = process("alias", fc, alias, name)
                if output["rc"] == 0:
                    ui.notify(f"Alias: {alias} added", type='positive')
                else:
                    ui.notify("Something went wrong!", type='negative')

            if fc == "del" and name and alias:
                output = process("alias", fc, alias, name)
                if output["rc"] == 0:
                    ui.notify(f"Alias: {alias} removed", type='positive')
                else:
                    ui.notify("Something went wrong!", type='negative')

        
        def __pswd_change(name, new_pswd):
            """Change password and handle system process."""
            if len(new_pswd) > 5:
                    output = process("email", "update", name, new_pswd)
                    if output["rc"] == 0:
                        ui.notify("Password changed", type='positive')
                    else:
                        ui.notify("Something went wrong!", type='negative')
            else:
                ui.notify("Password must be at least 6 characters", type='negative')
            
        
        if fc == "add_alias" and alias:
            fc = "add"
            __alias(fc, name, alias)

        elif fc == "del_alias" and alias:
            fc = "del"
            __alias(fc, name, alias)

        elif fc == "pswd_change" and new_pswd:
            __pswd_change(name, new_pswd)

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate the format of an email address."""
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(email_regex, email) is not None
#print(overview())
