#!/bin/bash

init_backend() {
    if [ -d ./venv ]; then 
        echo "Virtual environment already exists, skipping."
    else
        echo "Creating virtual environment."
        python -m pip install virtualenv
        virtualenv venv --python=python3
        venv/bin/pip install -r backend/requirements.txt

        # Apply migrations
        venv/bin/python backend/manage.py migrate

        # Create superuser
        export DJANGO_SUPERUSER_USERNAME=admin
        export DJANGO_SUPERUSER_PASSWORD=1234
        export DJANGO_SUPERUSER_EMAIL=admin@example.com
        venv/bin/python backend/manage.py createsuperuser --no-input --displayName "Admin" --githubUrl "https://github.com/uofa-cmput404" 
    fi

    # Apply migrations again (just in case)
    venv/bin/python backend/manage.py migrate
}

init_frontend() {
    echo "Installing frontend dependencies."
    cd frontend || exit
    npm install
    cd ..
}

# cleanup() {
#     echo "Stopping backend and frontend..."
#     kill -9 $(ps -A | grep python | awk '{print $1}')
#     kill -9 $(ps -A | grep npm | awk '{print $1}')
#     kill -9 $(ps -A | grep vite | awk '{print $1}')
# }



start_parallel() {
    # trap cleanup SIGINT

    echo "Starting backend + frontend in parallel."
    venv/bin/python backend/manage.py runserver 0.0.0.0:8000 &
    BACKEND_PID=$!
    cd frontend || exit
    npm run dev &
    FRONTEND_PID=$!
    cd ..

    # Manual loop to periodically check if the processes have terminated
 
}


# Call the functions
init_backend
init_frontend
start_parallel
