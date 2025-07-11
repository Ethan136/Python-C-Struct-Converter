import sys

def generate_struct_or_union_code(structure_type):
    """Handles the logic for generating a C++ struct or union."""
    if structure_type not in ["struct", "union"]:
        print("Invalid structure type specified.")
        return

    print(f"\n--- C++ {structure_type.capitalize()} Generator ---")
    try:
        name = input(f"Enter the name for your {structure_type} (e.g., MyData): ")
        if not name:
            print(f"{structure_type.capitalize()} name cannot be empty.")
            return

        members = []
        print(f"Enter the members of the {structure_type}, one per line, in the format 'type name' (e.g., 'int my_number').")
        print("Press Enter on an empty line when you are done.")
        while True:
            member_line = input(f"Member for {name}: ")
            if not member_line:
                break
            parts = member_line.split()
            if len(parts) < 2: # Allow for pointers like 'char *'
                print("Invalid format. Please use 'type name'.")
                continue
            
            # Handle cases like 'unsigned int'
            type_name = " ".join(parts[:-1])
            var_name = parts[-1]
            members.append((type_name, var_name))

        if not members:
            print(f"No members added. Aborting {structure_type} creation.")
            return

        variable_name = input(f"Enter a variable name for your {name} instance (e.g., myInstance): ")
        if not variable_name:
            variable_name = f"my{name.capitalize()}"
            print(f"No variable name given, defaulting to '{variable_name}'.")

        # --- Generate C++ Code ---
        print("\n--- Generated C++ Code ---")

        # Definition
        cpp_code = f"// 1. {structure_type.capitalize()} Definition\n"
        cpp_code += f"{structure_type} {name} {{\n"
        for m_type, m_name in members:
            cpp_code += f"    {m_type} {m_name};\n"
        cpp_code += "};\n\n"

        # Variable initialization
        cpp_code += f"// 2. Variable Initialization\n"
        
        if structure_type == "struct":
            print("Enter the values for each member:")
            values = []
            for m_type, m_name in members:
                val = input(f"  {m_type} {m_name}: ")
                # Add quotes for string types
                if m_type in ["std::string", "string", "char*"]:
                    values.append(f'\"{val}\"')
                else:
                    values.append(val)
            cpp_code += f"{name} {variable_name} = {{{', '.join(values)}}};\n"
        
        elif structure_type == "union":
            print("For a union, you can only initialize the first member.")
            first_member_type, first_member_name = members[0]
            val = input(f"  Value for the first member ({first_member_type} {first_member_name}): ")
            # Add quotes for string types
            if first_member_type in ["std::string", "string", "char*"]:
                formatted_val = f'\"{val}\"' 
            else:
                formatted_val = val
            cpp_code += f"{name} {variable_name} = {{{formatted_val}}};\n"


        print(cpp_code)
        print("--------------------------\n")

    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation cancelled. Returning to main menu.")


def main():
    """Main function to run the interactive tool."""
    print("Welcome to the C++ Data Structure Code Generator!")
    while True:
        print("What would you like to generate?")
        print("  1. A C++ struct")
        print("  2. A C++ union")
        print("  q. Quit")
        choice = input("Enter your choice (1, 2, or q): ")

        if choice == '1':
            generate_struct_or_union_code("struct")
        elif choice == '2':
            generate_struct_or_union_code("union")
        elif choice.lower() == 'q':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.\n")

if __name__ == "__main__":
    main()