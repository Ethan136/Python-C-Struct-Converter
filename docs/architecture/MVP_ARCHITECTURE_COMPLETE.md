# MVP Architecture - Complete Guide (Up-to-date)

## Overview

This document explains the current MVP design for the C Struct Converter app, including AST-based parsing, layout calculators, real-time GUI behavior, and Presenter context management.

## Architecture Layers

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│    View     │◄──►│  Presenter   │◄──►│   Model     │
│  (GUI)      │    │ (Logic)      │    │ (Business)  │
└─────────────┘    └──────────────┘    └─────────────┘
```

## 1. Model Layer (`src/model/`)

### 🎯 **Core responsibilities**
- **Pure Business Logic**: Handles C++ struct parsing and memory layout calculations
- **Data Processing**: Parses hexadecimal data and converts to structured data
- **No UI Dependencies**: Completely independent of user interface

### 📋 **Main components**

#### `struct_model.py`
Core orchestration over parsing/layout/hex parsing:
- `StructModel`: holds `struct_name`, `members`, `layout`, `total_size`, `struct_align`, `member_values`
- `load_struct_from_file()`: uses `parse_struct_definition()`; stores original content for AST regeneration
- `calculate_layout(members, pack_alignment=None)`: legacy and AST-aware path
- `parse_hex_data()`: left-pads hex and decodes fields (bitfield-aware)
- Manual mode: `validate_manual_struct()`, `calculate_manual_layout()`, `export_manual_struct_to_h()`

#### `struct_parser.py`
Parsers and AST structures:
- `MemberDef`, `StructDef`, `UnionDef`
- `parse_struct_definition[_v2]()` (legacy/flat), `parse_struct_definition_ast()`, `parse_union_definition_ast()`, `parse_c_definition_ast()`

### 🔧 **Technical characteristics**
- **Pure Functional Design**: Most methods are pure functions
- **Data-Driven**: Based on `TYPE_INFO` dictionary for type processing
- **Error Handling**: Throws exceptions for upper layers to handle
- **Stateless Operations**: No UI-related state preservation

### 📋 **Key functions**

#### 1. **Struct Definition Parsing**
```python
def parse_struct_definition(file_content):
    """Parses C++ struct definition"""
    # Uses regex to extract struct name and members
    # Returns struct_name and members list
```

#### 2. **Memory layout calculation**
```python
def calculate_layout(members, pack_alignment=None):
    # Accepts AST members (preferred) or legacy dict/tuple members
    # Delegates to StructLayoutCalculator / UnionLayoutCalculator
    # Returns (layout_items, total_size, effective_alignment)
```

#### 3. **Hexadecimal Data Parsing**
```python
def parse_hex_data(self, hex_data, byte_order):
    """Parses hexadecimal data into structured data"""
    # Converts hex string to bytes
    # Parses each member according to layout
    # Returns parsed values list
```

## 2. View Layer (`src/view/`)

### 🎯 **Core responsibilities**
- **User Interface**: Displays the GUI and handles user interactions
- **Passive Component**: Contains no business logic
- **Event Delegation**: Delegates user events to Presenter

### 📋 **Main components**

#### `struct_view.py`
Tkinter GUI with two tabs (load .h / manual struct):
- Shared hex grid builder, Treeview population, debug bytes display
- Layout Treeview shows name/type/offset/size/bit_offset/bit_size/is_bitfield
- Debug tab shows Presenter cache statistics and context debug info

### 🔧 **Technical Characteristics**
- **UI-Focused**: Pure user interface logic
- **Event-Driven**: Responds to user interactions
- **Presenter Communication**: Communicates with Presenter for actions
- **Display Logic**: Handles all visual updates

## 3. Presenter Layer (`src/presenter/`)

### 🎯 **Core responsibilities**
- **Application Logic**: Coordinates between Model and View
- **User Event Handling**: Processes user operations from View
- **Data Transformation**: Converts user input to Model-processable format
- **Error Handling**: Processes and displays error messages to users

### 📋 **Main components**

#### `struct_presenter.py`
Coordinates Model and View, and manages context/state:
- Hex chunk validation and processing via `InputFieldProcessor`
- LRU cache for manual layout computation; auto-clear timer controls
- Context with undo/redo history, UI options, and debug info; debounced updates to the View
- Observer pattern: Presenter observes Model and updates the View on changes

### 🔧 **Technical characteristics**
- **Event-Driven**: Responds to View user events
- **State Management**: Manages UI state and data flow
- **Error Handling**: Catches exceptions and displays user-friendly error messages
- **Data Transformation**: Converts data formats between Model and View

### 📋 **Key functions**

#### 1. **File browsing and loading**
```python
def browse_file(self):
    """Handles file browsing and loading logic"""
    # Shows file dialog
    # Calls model.load_struct_from_file()
    # Updates view display
    # Rebuilds hex input grid
```

#### 2. **Input validation and conversion**
```python
def parse_hex_data(self):
    """Handles hex input validation and conversion"""
    # Validates input format
    # Converts user input to memory format
    # Handles byte order
    # Calls model.parse_hex_data()
```

#### 3. **UI state management**
```python
def on_unit_size_change(self, *args):
    """Handles unit size changes"""
    # Rebuilds hex input grid
    # Updates UI state
```

## 4. Configuration Layer (`src/config/`)

### 🎯 **Core responsibilities**
- **Application Configuration**: Manages application settings
- **Internationalization**: Handles localized UI strings
- **String Management**: Provides centralized string handling

### 📋 **Main components**

#### `ui_strings.py`
**String management utilities:**
- Loads UI strings from XML files
- Provides string retrieval with fallback handling

#### `ui_strings.xml`
**Localized UI strings:**
- Contains all user-facing strings
- Supports internationalization

## Detailed component comparison

### StructModel vs StructPresenter: Function Differences

| Function Area | StructModel | StructPresenter |
|---------------|-------------|-----------------|
| **File Parsing** | ✅ Parses C/C++ struct/union syntax | ❌ Does not directly parse files |
| **Memory Calculation** | ✅ Calculates layout (struct/union), alignment, padding | ❌ Does not perform calculations |
| **Data Parsing** | ✅ Parses hex to structured data (bitfield-aware) | ❌ Does not directly parse data |
| **Input Validation** | ❌ Does not validate user input | ✅ Validates hex format, range |
| **UI Interaction** | ❌ No UI dependencies | ✅ Handles file dialogs, error display |
| **State Management** | ❌ No UI state | ✅ Manages context, grid rebuilding, debug | 
| **Error Handling** | ❌ Throws exceptions | ✅ Shows user-friendly error messages |
| **Data Transformation** | ❌ Pure data processing | ✅ Input format conversion, byte order handling |

## Collaboration flow

### 1. **File loading flow**
```
View (Browse Button) 
    ↓
Presenter.browse_file()
    ↓
Model.load_struct_from_file() → (also preserves file content for AST on demand)
    ↓
Presenter updates View display
```

### 2. **Data parsing flow**
```
View (Parse Button)
    ↓
Presenter.parse_hex_data()
    ↓ (Input validation and conversion)
Model.parse_hex_data() → Presenter updates View results and context
    ↓
Presenter updates View results
```

## Design principles

### StructModel principles
- **Single Responsibility**: Only responsible for struct parsing and data processing
- **Purity**: No dependencies on external state or UI
- **Testability**: Each method can be tested independently
- **Reusability**: Can be reused with different UI frameworks

### StructPresenter principles
- **Coordinator**: Coordinates interactions between Model and View
- **Transformer**: Converts data formats and processes user input
- **Error Handler**: Provides user-friendly error handling
- **State Manager**: Manages UI state and data flow

### View principles
- **UI-Focused**: Only contains user interface logic
- **Passive**: Does not contain business logic
- **Event Delegation**: Delegates user events to Presenter
- **Display Logic**: Handles all visual updates

## Extensibility considerations

### Adding New Features

#### Adding new struct type support
- **Model**: Extend `TYPE_INFO` dictionary, add parsing logic
- **Presenter**: No changes needed (unless special UI handling required)

#### Adding new input format support
- **Model**: Add parsing methods
- **Presenter**: Add input validation and conversion logic

#### Adding new output format support
- **Model**: Add formatting methods
- **Presenter**: Add output processing logic

## Benefits of MVP

1. **Maintainability**: Clear separation of concerns makes code easier to understand and modify
2. **Testability**: Each layer can be unit tested independently
3. **Reusability**: Model can be reused with different UI frameworks
4. **Scalability**: Easy to add new features without affecting existing code
5. **Team Development**: Different developers can work on different layers

## File organization

```
src/
├── __init__.py              # Package initialization
├── main.py                  # Application entry point
├── model/                   # Model layer (business logic)
│   ├── __init__.py
│   ├── layout.py            # Layout calculators and TYPE_INFO
│   ├── struct_parser.py     # Parsers and AST dataclasses
│   └── struct_model.py      # Orchestration and hex parsing
├── view/                    # View layer (UI)
│   ├── __init__.py
│   └── struct_view.py       # GUI implementation
├── presenter/               # Presenter layer (coordination)
│   ├── __init__.py
│   └── struct_presenter.py  # Application logic
└── config/                  # Configuration layer
    ├── __init__.py
    ├── ui_strings.py        # String management
    └── ui_strings.xml       # Localized strings
```

## Testing Strategy

- **Unit Tests**: Test each layer independently
- **Integration Tests**: Test layer interactions
- **End-to-End Tests**: Test complete user workflows

## Future Enhancements

1. **Multiple UI Frameworks**: Model can be reused with Qt, web UI, etc.
2. **Plugin Architecture**: Extensible struct type support
3. **Internationalization**: Full i18n support
4. **Configuration Management**: User preferences and settings

## Summary

The MVP architecture provides a clean separation of concerns:

- **StructModel** is the pure business logic layer, focused on data processing and calculations
- **StructPresenter** is the application logic layer, focused on user interaction and state management
- **StructView** is the UI layer, focused on display and user interaction
- **Configuration** layer manages application settings and internationalization

This separation ensures code maintainability, testability, and reusability, following SOLID principles and particularly the Single Responsibility Principle. 