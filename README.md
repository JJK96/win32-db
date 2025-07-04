# Win32 API database

This program can generate a database of Windows API function definitions/signatures based on C header files. This can be useful for compiling in situations where dynamic linking is not possible in the usual way.

## Method

Currently, I use `mingw` headers and libraries to obtain the data. But with minimal changes this could be changed to the Windows SDK provided by Microsoft if necessary.

## Dependencies

- mingw-w64
- ripgrep (rg)
