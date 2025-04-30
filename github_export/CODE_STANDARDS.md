# Code Standards and Best Practices

This document outlines the coding standards and best practices all team members should follow when contributing to the DARG project.

## Python Style Guidelines

1. **Follow PEP 8**
   - Use 4 spaces for indentation (no tabs)
   - Limit lines to 79 characters where possible
   - Use appropriate naming conventions:
     - `snake_case` for variables and functions
     - `PascalCase` for classes
     - `UPPER_CASE` for constants

2. **Docstrings**
   - Every function, class, and module should have a docstring
   - Use the following format for function docstrings:

   ```python
   def function_name(param1, param2):
       """
       Brief description of function.
       
       Args:
           param1 (type): Description of param1
           param2 (type): Description of param2
           
       Returns:
           type: Description of return value
           
       Raises:
           ExceptionType: When and why this exception is raised
       """
   ```

3. **Imports**
   - Group imports in the following order:
     1. Standard library imports
     2. Related third-party imports
     3. Local application imports
   - Sort imports alphabetically within each group

## Streamlit-Specific Guidelines

1. **Session State Management**
   - Use `st.session_state` for maintaining state between reruns
   - Initialize all session state variables at the top of the script
   - Use descriptive names for session state variables

2. **UI Organization**
   - Use `st.sidebar` for navigation and filters
   - Group related UI elements with `st.expander` where appropriate
   - Use meaningful headers and subheaders to structure the page

3. **Performance Considerations**
   - Cache expensive operations with `@st.cache_data` or `@st.cache_resource`
   - Avoid unnecessary recomputation during UI interactions
   - Load data efficiently, preferably in chunks when dealing with large datasets

## Data Access Layer

1. **Always use the data_access.py module**
   - Never make direct API calls outside this module
   - Use the provided functions for all data operations

2. **Error Handling**
   - Handle all potential data access errors gracefully
   - Provide meaningful error messages to users
   - Log detailed error information for debugging

3. **Fallback Mechanisms**
   - Understand the fallback mechanisms in place when Supabase is unavailable
   - Don't modify these mechanisms without team discussion

## Component Development

1. **Reusability**
   - Design components to be reusable across multiple pages
   - Use parameters to make components flexible
   - Document expected input parameters and return values

2. **Naming Conventions**
   - Use descriptive names that reflect the component's purpose
   - Follow the format `component_name.py` for component files

3. **Testing**
   - Test components with various input combinations
   - Verify they handle edge cases appropriately

## Git Workflow

1. **Branches**
   - Always create a new branch for each feature or fix
   - Use the naming conventions in CONTRIBUTING.md

2. **Commits**
   - Make small, focused commits that do one thing
   - Write clear commit messages
   - Reference task IDs where applicable

3. **Pull Requests**
   - Keep PRs focused on a single feature or fix
   - Ensure all GitHub Actions checks pass
   - Request review from appropriate team members

## Security Considerations

1. **Environment Variables**
   - Never hardcode sensitive information
   - Always use environment variables for credentials

2. **Input Validation**
   - Validate all user input before processing
   - Be particularly careful with any data used in SQL queries

3. **Access Control**
   - Respect the tiered access control system
   - Don't bypass access restrictions in your code
