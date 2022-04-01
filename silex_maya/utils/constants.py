import re

# Regex used to expand and capture syntaxes for sequences like #### or <UDIM> ...
MATCH_FILE_SEQUENCE = [
    re.compile(r"^.+\W(\<.+\>)\W.+$"),  # Matches V-ray's <Whatever> syntax
    re.compile(r"^.+[^\w#](#+)\W.+$"),  # Matches V-ray's ####  syntax
    re.compile(r"^.+(\<.+\>)[\W_].+$"),  # Matches unique case for macula 
]
