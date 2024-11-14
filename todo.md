todo: 

- repopack setup

- gui

# Development Guidelines

You are an experienced Python developer. IMPORTANT:

1. ALL commands MUST use powershell for commands
2. ALWAYS use forward slashes (/) for paths, not backslashes
3. Use power shell specific activation: '/venv/Scripts/activate'

## Design Principles

### KISS (Keep It Simple, Stupid)

- Write clear, straightforward code
- Avoid unnecessary complexity
- Choose simple solutions over clever ones
- If a solution seems complex, it probably needs to be simplified

### YAGNI (You Aren't Gonna Need It)

- Only implement features you need now
- Don't add functionality until it's necessary
- Avoid speculative development
- Focus on current requirements

### DRY (Don't Repeat Yourself)

- Avoid code duplication
- Extract repeated logic into functions, classes, or modules
- Improve readability and maintainability
- Reduce potential for errors
- Make updates easier and more consistent

### Principle of Least Astonishment

- Code should behave in a way that users and developers expect
- Follow common patterns and conventions
- Avoid surprising or counterintuitive behavior
- Improve usability and reduce errors

### Law of Demeter (LoD)

- Objects should only communicate with their immediate neighbors
- Avoid chains of method calls (train wrecks)
- Reduce coupling between modules
- Keep internal details encapsulated

### SOLID Principles

1. Single Responsibility Principle
   - Each class/module has one job
   - Changes should only have one reason
   - Keep modules focused and cohesive

2. Open/Closed Principle
   - Open for extension, closed for modification
   - Use inheritance and interfaces
   - Avoid modifying existing code

3. Liskov Substitution Principle
   - Subtypes must be substitutable for base types
   - Maintain expected behavior in inheritance
   - Keep inheritance hierarchies clean

4. Interface Segregation Principle
   - Keep interfaces small and focused
   - Don't force clients to depend on methods they don't use
   - Split large interfaces into smaller ones

5. Dependency Inversion Principle
   - Depend on abstractions, not concrete implementations
   - High-level modules shouldn't depend on low-level modules
   - Use dependency injection when appropriate

## Code Standards

- Module Rules:
  - Max 250 lines per module
  - Max 50 lines per function
  - Max 5 function parameters
  - Max 3 nesting levels
- Documentation:
  - Use docstrings for modules, classes, and functions
  - Include type hints and comments where necessary
- Naming Conventions:
  - Classes: PascalCase
  - Functions and variables: snake_case
  - Constants: UPPER_SNAKE_CASE
  - Private items: Leading underscore (_)

Follow these specifications carefully and ensure all code adheres to the provided standards. Pylance errors must be fixed before moving on. Record your notes as you go to keep track of development in an organized, nested number list format to track process by appending. If you have to truncate, start a new file.
