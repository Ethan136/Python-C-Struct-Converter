# C++ Struct Memory Parser - Architecture Documentation

## Overview

This application follows the **Model-View-Presenter (MVP)** architectural pattern to provide a clean separation of concerns and maintainable codebase.

## Architecture Layers

### 1. Model Layer (`src/model/`)
**Responsibility**: Core business logic and data management

- **`struct_model.py`**: Contains the core struct parsing logic
  - `StructModel` class: Main data model
  - `parse_struct_definition()`: Parses C++ struct definitions
  - `calculate_layout()`: Computes memory layout with padding
  - `parse_hex_data()`: Interprets hexadecimal data

- **`STRUCT_PARSING.md`**: Documentation for struct parsing mechanism

### 2. View Layer (`src/view/`)
**Responsibility**: User interface and display logic

- **`struct_view.py`**: Tkinter GUI implementation
  - `StructView` class: Main GUI window
  - File browser interface
  - Struct layout display
  - Hex data input grid
  - Results display area

### 3. Presenter Layer (`src/presenter/`)
**Responsibility**: Application logic and coordination

- **`struct_presenter.py`**: Coordinates between Model and View
  - `StructPresenter` class: Main presenter
  - Handles user events from View
  - Processes data through Model
  - Updates View with results

### 4. Configuration Layer (`src/config/`)
**Responsibility**: Application configuration and internationalization

- **`ui_strings.py`**: String management utilities
- **`ui_strings.xml`**: Localized UI strings

## Data Flow

```
User Action → View → Presenter → Model
                ↑                    ↓
User Display ← View ← Presenter ← Model
```

### Example Flow:
1. User clicks "Browse" button
2. View calls `presenter.browse_file()`
3. Presenter opens file dialog and calls `model.load_struct_from_file()`
4. Model parses the file and returns struct data
5. Presenter calls `view.show_struct_layout()` to update display
6. View displays the parsed struct information

## Key Design Principles

### 1. Separation of Concerns
- **Model**: Pure business logic, no UI dependencies
- **View**: Pure UI logic, no business logic
- **Presenter**: Coordinates between Model and View

### 2. Dependency Direction
- View depends on Presenter (interface)
- Presenter depends on Model and View (interfaces)
- Model has no dependencies on other layers

### 3. Testability
- Each layer can be tested independently
- Mock objects can easily replace dependencies
- Business logic is isolated from UI framework

## File Organization

```
src/
├── __init__.py              # Package initialization
├── main.py                  # Application entry point
├── model/                   # Model layer
│   ├── __init__.py
│   ├── struct_model.py      # Core business logic
│   └── STRUCT_PARSING.md    # Model documentation
├── view/                    # View layer
│   ├── __init__.py
│   └── struct_view.py       # GUI implementation
├── presenter/               # Presenter layer
│   ├── __init__.py
│   └── struct_presenter.py  # Application logic
└── config/                  # Configuration layer
    ├── __init__.py
    ├── ui_strings.py        # String management
    └── ui_strings.xml       # Localized strings
```

## Benefits of MVP Architecture

1. **Maintainability**: Clear separation makes code easier to understand and modify
2. **Testability**: Each layer can be unit tested independently
3. **Reusability**: Model can be reused with different UI frameworks
4. **Scalability**: Easy to add new features without affecting existing code
5. **Team Development**: Different developers can work on different layers

## Testing Strategy

- **Unit Tests**: Test each layer independently
- **Integration Tests**: Test layer interactions
- **End-to-End Tests**: Test complete user workflows

## Future Enhancements

1. **Multiple UI Frameworks**: Model can be reused with Qt, web UI, etc.
2. **Plugin Architecture**: Extensible struct type support
3. **Internationalization**: Full i18n support
4. **Configuration Management**: User preferences and settings 