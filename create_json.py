import re
import json
import subprocess
from pathlib import Path
from config import mingw_lib_path, mingw_headers_path, objdump
import logging

class InvalidDefinition(Exception):
    pass

class Definition:
    def __init__(self, definition_str, dll=None):
        self.definition_str = definition_str
        self.dll = dll
        if not self.is_valid():
            raise InvalidDefinition()
        try:
            self.parse()
        except Exception as e:
            logging.debug(f"Could not parse: {self.definition_str}")
            raise InvalidDefinition(e)

    def is_valid(self):
        if "virtual" in self.definition_str:
            return False
        if self.definition_str.startswith('#'):
            return False
        return self.definition_str.count('(') == 1

    def parse(self):
        types, _, args = self.definition_str.partition('(')
        types = list(filter(lambda x:x and x != "WINBASEAPI", types.split(' ', )))
        self.function_name = types[-1]
        self.types = types[:-1]
        self.literal_args = args[:-2]
        self.variables = []
        if self.literal_args.lower() != "void":
            for arg in self.literal_args.split(", "):
                if not ' ' in arg:
                    continue
                self.variables.append(arg.split(' ')[1].lstrip('*'))

    def __str__(self):
        return self.definition_str

def dll_to_lib(dll):
    return "lib"+dll[:-3] + "a"

def get_symbols_for_dll(dll):
    lib = Path(mingw_lib_path) / dll_to_lib(dll)
    cmd = [objdump, "-t", lib, "-j.text"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.stdout.decode().splitlines():
        if not re.search(r"\(scl +2\)", line):
            continue
        symbol = line[67:]
        if symbol[0] == '_':
            continue
        if not re.match(r'^[A-Za-z0-9_]+$', symbol):
            continue
        yield symbol
    
def get_definitions_for_dll(dll):
    regex = r'\b\(' + '|'.join(get_symbols_for_dll(dll)) + r'\)\b'
    cmd = ["rg", "-IN", regex, mingw_headers_path]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in p.stdout.splitlines():
        try:
            line = line.decode().strip()
        except UnicodeDecodeError:
            logging.debug("Could not decode ", str(line))
            continue
        if "__mingw_" in line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("/*"):
            continue
        try:
            yield Definition(line, dll=dll)
        except InvalidDefinition:
            continue
        

def create_json(dll):
    output = {}
    for d in get_definitions_for_dll(dll):
        if not re.match(r'^[A-Za-z0-9_]+$', d.function_name):
            continue
        output[d.function_name] = d.definition_str
    output = {k:v for k,v in sorted(output.items(), key=lambda x:x[0])}
    with open(dll + ".json", 'w') as f:
        json.dump(output, f)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate JSON file with all function signatures in the given DLL")
    parser.add_argument("dll")
    args = parser.parse_args()

    create_json(args.dll)

