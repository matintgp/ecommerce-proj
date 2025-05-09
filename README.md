steps for start project in ur system:
1. Clone the repository
    ```bash
    git clone https://github.com/yourusername/ecommerce-drf.git
    cd ecommerce-drf
    ```

2. Create and activate virtual environment
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```

4. Make migrations:
    ```bash
    python manage.py makemigrations
    ```

5. Run migrations
    ```bash
    python manage.py migrate
    ```

6. Start the development server
    ```bash
    python manage.py runserver
    ```


create superuser if needed:
    ```bash
    python manage.py createsuperuser
    ```



The server will start at http://localhost:8000