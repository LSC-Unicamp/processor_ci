# Contributing to the Project  

Thank you for considering contributing to the project! We’re happy to welcome contributions from anyone interested in improving this project. Before you begin, please read this guide to understand how to contribute effectively.  

## How to Contribute  

1. **Fork the Repository**  
   Fork this repository to your GitHub account.  

2. **Clone the Repository**  
   Clone your forked repository to your local development environment.  

   ```bash  
   git clone https://github.com/YOUR_USERNAME/processor_ci.git  
   cd processor_ci  
   ```  

3. **Create a Branch**  
   Create a branch for your contribution. Make sure to choose a descriptive name, such as `feature/new-feature` or `fix/bug-fix`.  

   ```bash  
   git checkout -b my-contribution  
   ```  

4. **Make Changes**  
   Implement the necessary changes in the code while adhering to the project standards.  

5. **Test Your Changes**  
   Ensure your changes do not introduce issues. Run the existing tests and add new ones if necessary.  

6. **Commit and Push**  
   Commit your changes with a clear and concise message explaining what was modified. Then, push your changes to your forked repository.  

   ```bash  
   git add .  
   git commit -m "Added a new feature"  
   git push origin my-contribution  
   ```  

7. **Create a Pull Request**  
   Open a Pull Request (PR) to the main branch of the original repository. Clearly describe the changes you made and include any relevant details, such as context and impact.  

8. **Review and Discussion**  
   The project team will review your PR and may request changes or clarifications. Be ready to collaborate and adjust your code as needed.  

9. **Approval and Merge**  
   Once the review is successful and approved by the team, your PR will be merged into the main repository.  

10. **Celebrate**  
   Congratulations! Your contribution has been successfully merged into the project.  

## Contribution Guidelines  

- Follow the project’s coding standards.  
- Keep commit messages clear and descriptive.  
- Avoid making too many changes in a single PR to simplify reviews.  
- Add tests to cover code changes, where applicable.  
- Only PRs that pass the checks will be accepted.  

## Coding Standards  

- Indentation: tabs (4 spaces).  
- Lines up to 88 characters.  
- PEP 8 compliance.  
- Use docstrings for functions, methods, and files.  
- Whenever possible, include type hints for parameters and return values.  

## Formatting and Linting Tools  

- **Blue**:  
  ```bash  
  blue --check .  
  ```  
- **Pylint**:  
  ```bash  
  pylint $(git ls-files '*.py' ':!utils/*') --max-locals=30 --disable=duplicate-code,import-error  
  ```  

## Communication  

- If you have any questions or need help, open an issue in the repository.  
- Thank you for contributing to make the project better!  

## License  

By contributing to this project, you agree that your contributions will be licensed under the same license as the project. See the [license](https://github.com/LSC-Unicamp/processor_ci/blob/main/LICENSE) for details.  
