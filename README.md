# C++ Struct Memory Parser (GUI Version)

This project provides a graphical user interface (GUI) tool built with Python and Tkinter to parse the memory layout of a C++ struct. It can read a C++ header file, calculate the struct's memory layout including padding based on standard alignment rules, and then interpret a raw hexadecimal string to show the values of each member.

## Features

- **Graphical User Interface**: Easy-to-use window for all operations.
- **File Browser**: Select C++ header (`.h`) files directly from your file system.
- **Automatic Layout Calculation**: Parses a C++ `struct` definition and automatically calculates:
  - The size and alignment of each member.
  - The required memory padding between members.
  - The final total size of the struct.
- **Hexadecimal Data Parsing**: Takes a continuous string of hex data and maps it to the struct members according to the calculated layout.
- **Little-Endian Conversion**: Correctly interprets the byte sequence for each member in little-endian format.
- **Clear Results Display**: Shows the parsed values for each member in both decimal and hexadecimal formats.

## Requirements

- **Python 3**: The script is written for Python 3.
- **Tkinter**: The GUI is built using the `tkinter` library, which is standard in most Python installations. If it's missing (which can happen on some macOS or Linux minimal installs), you may need to install it separately.

  For macOS, if you encounter errors, you can install `python-tk` via Homebrew:
  ```bash
  brew install python-tk
  ```

## How to Use

1.  **Run the Application**:
    Open your terminal and execute the following command:
    ```bash
    python3 gui_parser.py
    ```
    *(Note: Use `python3`. If that fails, try `python`)*

2.  **Load a Struct Definition**:
    - The application window will appear.
    - Click the **"Browse..."** button.
    - Select a C++ header file (e.g., the included `example.h`) that contains a valid `struct` definition.

3.  **Review the Layout**:
    - Once loaded, the "Struct Layout" area will display the parsed information: the struct's total size, alignment, and the offset, size, and type of each member.

4.  **Input Hex Data**:
    - The application will show how many hexadecimal characters are expected based on the struct's total size.
    - Paste your continuous hexadecimal string into the "Hex Data Input" field.

5.  **Parse and View Results**:
    - Click the **"Parse Data"** button.
    - The "Parsed Values" area will populate with a table showing each member's name, its parsed value (in decimal or as `true`/`false` for booleans), and its original little-endian hex representation.

## Example File

An `example.h` file is included to demonstrate the functionality with a struct that requires memory padding.