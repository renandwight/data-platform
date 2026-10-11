# Resolve project directory
set -l PROJECT_ROOT (path resolve (dirname (status filename))/..)

# Navigate to project
cd $PROJECT_ROOT

# Activate virtual environment
source .venv/bin/activate.fish

# Load local credentials
source .env.fish

# PostgreSQL connection
set -gx POSTGRES_HOST localhost
set -gx POSTGRES_PORT 5432
set -gx POSTGRES_DB analytics
set -gx POSTGRES_USER data_pipeline

# dbt PostgreSQL credentials
set -gx DBT_ENV_SECRET_PG_PASSWORD $POSTGRES_PASSWORD

# Navigate to dbt project
cd dbt/data_platform

echo "Data platform development environment ready."