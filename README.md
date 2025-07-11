# C++ Struct Memory Parser (GUI Version - MVP Architecture)

This project provides a graphical user interface (GUI) tool built with Python and Tkinter to parse the memory layout of a C++ struct. It has been refactored to follow the Model-View-Presenter (MVP) architectural pattern for better modularity, maintainability, and testability.

## Architecture: Model-View-Presenter (MVP)

- **Model (`src/model/`)**: Contains the core business logic, data structures, and data manipulation. It's independent of the UI.
  - `struct_model.py`: Handles parsing C++ struct definitions, calculating memory layouts (including padding), and interpreting raw hexadecimal data based on endianness.

- **View (`src/view/`)**: Responsible for displaying the user interface and handling user interactions. It's passive and doesn't contain any business logic.
  - `struct_view.py`: Implements the Tkinter GUI elements and methods to update the display and retrieve user input.

- **Presenter (`src/presenter/`)**: Acts as an intermediary between the Model and the View. It handles user events from the View, retrieves data from the Model, and updates the View accordingly. It contains the application's presentation logic.
  - `struct_presenter.py`: Manages the flow of data and events between `StructModel` and `StructView`.

## Features

- **Graphical User Interface**: Easy-to-use window for all operations.
- **File Browser**: Select C++ header (`.h`) files directly from your file system.
- **Automatic Layout Calculation**: Parses a C++ `struct` definition and automatically calculates:
  - The size and alignment of each member.
  - The required memory padding between members.
  - The final total size of the struct.
- **Chunked Hexadecimal Data Input**: Allows inputting hex data in user-defined chunks (1, 4, or 8 bytes) for better readability and ease of entry.
- **Configurable Byte Order**: Choose between Little Endian and Big Endian for data interpretation.
- **Clear Results Display**: Shows the parsed values for each member in both decimal and hexadecimal formats.

## Requirements

- **Python 3**: The script is written for Python 3.
- **Tkinter**: The GUI is built using the `tkinter` library, which is standard in most Python installations. If it's missing (which can happen on some macOS or Linux minimal installs), you may need to install it separately.

  For macOS, if you encounter errors, you can install `python-tk` via Homebrew:
  ```bash
  brew install python-tk
  ```

## How to Use

1.  **Navigate to the `src` directory**:
    ```bash
    cd src
    ```

2.  **Run the Application**:
    Execute the `main.py` script:
    ```bash
    python3 main.py
    ```
    *(Note: Use `python3`. If that fails, try `python`)*

3.  **Load a Struct Definition**:
    - The application window will appear.
    - Click the **"Browse..."** button.
    - Select a C++ header file (e.g., the `example.h` located in the project root) that contains a valid `struct` definition.

4.  **Review the Layout**:
    - Once loaded, the "Struct Layout" area will display the parsed information: the struct's total size, alignment, and the offset, size, and type of each member.

5.  **Input Hex Data**:
    - Choose your preferred "Input Unit Size" (1, 4, or 8 Bytes) and "Byte Order" (Little Endian or Big Endian).
    - The application will show how many hexadecimal characters are expected based on the struct's total size.
    - Fill in the generated input fields with your hexadecimal data.

6.  **Parse and View Results**:
    - Click the **"Parse Data"** button.
    - The "Parsed Values" area will populate with a table showing each member's name, its parsed value, and its original raw hex representation.

## Example File

An `example.h` file is included in the project root to demonstrate the functionality with a struct that requires memory padding.
