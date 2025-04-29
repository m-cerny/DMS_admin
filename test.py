import re

# Raw data
raw_data = """
* m.cerny@redandblack.cz ( 0 / ~ ) [0%]
    [ aliases -> sdasdasd@adasd.cz ]

* info@lepsistavy.cz ( 0 / 100M ) [0%]
    [ aliases -> test@ls.cz ]

* test@test.test ( 0 / ~ ) [0%]
"""

# Pattern to match email blocks
email_block_pattern = re.compile(
    r"\* (?P<email>\S+) \(\s*(?P<used>\S+)\s*/\s*(?P<quota>\S+)\s*\) \[(?P<percent>\d+)%\](?:\s*\[\s*aliases\s*->\s*(?P<aliases>[^\]]+)\])?",
    re.MULTILINE
)

# Parse data into a dict with email as key
email_dict = {}

for match in email_block_pattern.finditer(raw_data):
    data = match.groupdict()
    email_dict[data["email"]] = {
        "used": data["used"],
        "quota": data["quota"],
        "percent_used": int(data["percent"]),
        "aliases": [a.strip() for a in data["aliases"].split(",")] if data["aliases"] else []
    }

print(email_dict)
