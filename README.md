# C++ Struct/Union 程式碼產生器

這是一個 Python 腳本，提供了一個簡單的命令列介面，用於自動產生 C++ 的 `struct` 和 `union` 的定義及初始化程式碼。

## 功能

*   **互動式介面**: 透過問答方式引導使用者輸入必要的資訊。
*   **C++ `struct` 產生**:
    *   自訂 `struct` 名稱。
    *   自訂成員變數的型別和名稱。
    *   產生 `struct` 的定義。
    *   產生一個實例變數並使用使用者提供的值進行初始化。
*   **C++ `union` 產生**:
    *   自訂 `union` 名稱。
    *   自訂成員變數的型別和名稱。
    *   產生 `union` 的定義。
    *   產生一個實例變數並使用使用者提供的值初始化其第一個成員。
*   **自動處理字串**: 在為 `std::string` 或 `char*` 型別賦值時，會自動加上雙引號。

## 如何使用

1.  **環境要求**: 只需要一個可以執行 Python 的環境。
2.  **執行腳本**: 在您的終端機中，導航到包含 `cpp_struct_generator.py` 的目錄，然後執行以下命令：

    ```bash
    python cpp_struct_generator.py
    ```

3.  **遵循提示**: 程式會啟動一個選單，您可以選擇要產生 `struct` (輸入 1) 還是 `union` (輸入 2)。接著，只需按照終端中的提示輸入對應的資訊即可。

## 範例

### 產生一個 C++ Struct

假設您執行腳本並選擇 `1`，互動過程可能如下：

```
--- C++ Struct Generator ---
Enter the name for your struct (e.g., MyData): Student
Enter the members of the struct, one per line, in the format 'type name' (e.g., 'int my_number').
Press Enter on an empty line when you are done.
Member for Student: std::string name
Member for Student: int id
Member for Student: 
Enter a variable name for your Student instance (e.g., myInstance): newStudent

Enter the values for each member:
  std::string name: Alice
  int id: 101
```

**產生的 C++ 程式碼:**

```cpp
// 1. Struct Definition
struct Student {
    std::string name;
    int id;
};

// 2. Variable Initialization
Student newStudent = {"Alice", 101};
```

### 產生一個 C++ Union

假設您在主選單選擇 `2`，互動過程可能如下：

```
--- C++ Union Generator ---
Enter the name for your union (e.g., MyData): Data
Enter the members of the union, one per line, in the format 'type name' (e.g., 'int my_number').
Press Enter on an empty line when you are done.
Member for Data: int i
Member for Data: float f
Member for Data: 
Enter a variable name for your Data instance (e.g., myInstance): myData

For a union, you can only initialize the first member.
  Value for the first member (int i): 123
```

**產生的 C++ 程式碼:**

```cpp
// 1. Union Definition
union Data {
    int i;
    float f;
};

// 2. Variable Initialization
Data myData = {123};
```
