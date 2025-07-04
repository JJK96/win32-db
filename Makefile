dlls = kernel32.dll ntdll.dll advapi32.dll msvcrt.dll

all: version_details.txt $(addsuffix .json,$(dlls))

version_details.txt:
	apt show mingw-w64 | grep -i version > $@

%.json:
	python create_json.py $(basename $@)
