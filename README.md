## Base instructions for a dbt-Snowflake project setup

## Setup (dbt core)

1. Create an empty repository in Github.

2. Clone the repository locally.
```bash
# Clone the repository
git clone git@github.com:<accountName>/<repoName>.git
```

3. Install dbt in a virtual environment. Use [uv](https://docs.astral.sh/uv/) to create a virtual
environmeny and install the dependencies. To install `uv` run the following command:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For other installtion methods, see [installing uv](https://docs.astral.sh/uv/getting-started/installation/).
Once `uv` is installed, run the following command to create a virtual environment and install the dependencies:
```bash
# Create virtual environment
uv venv --python=3.12
```
This will create a virtual environment in the `.venv` directory at the root of the repository.

4. Activate the virtual environment.
```bash
# Activate virtual environment
source .venv/bin/activate
```

5. Configure the pyproject.toml file with project dependencies.

6. Install the project in development mode.
```bash
# Install the project
uv pip install -e .

# Or install with development dependencies
uv pip install -e ".[dev]"
```

7. Set up environment variables for Snowflake authentication.
Create a `.env` file in the root of the repository and add all the variables.
Then create an `.envrc` file with the following content:
```bash
# direnv configuration
dotenv
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi
unset PS1
```

Install direnv (if not already installed):
```bash
# Install direnv on macOS
brew install direnv
# Install direnv on Ubuntu/Debian
sudo apt-get install direnv
# Add to your shell (add to ~/.bashrc, ~/.zshrc, etc.)
eval "$(direnv hook bash)"  # for bash
# or
eval "$(direnv hook zsh)"   # for zsh
```
Then run:
```bash
# Allow direnv in this directory
direnv allow
```
Note: If you see a warning about "PS1 cannot be exported", this is normal and can be safely ignored.
It's related to shell prompt customization and doesn't affect the functionality of the environment variables.

8. Initialize dbt by running the following command.

```bash
# Verify dbt installation
dbt init my_dbt_project
```

9. Create a .dbt folder in the root and add a profiles.yml.

10. Verify the installation by running the following command.
```bash
# Verify dbt installation
dbt --version
```

11. Create a .pre-commit-config.yaml file in the root.

12. Check and install pre-commit hooks by running the following command:
```bash
# Check pre-commit
pre-commit --version
# Install pre-commit hooks
pre-commit install
```
**now pre-commit will run automatically on git commit!**

13. Add the .gitignore file with the path to be ignore.

14. Ensure the profiles.yml and the .env variables are configured correctly. Make sure you have a
Snowflake key-pair created. Set the RSA_PUBLIC_KEY in Snowflake and add the SNOWFLAKE_PRIVATE_KEY_PATH
into the .env file.

15. Run the following commands to test connection and build the dbt project.
```bash
# Test connection
dbt debug
# Build dbt project
dbt build
```

## Instructions for Snowflake Connector
