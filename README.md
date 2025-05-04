# README for Ecommerce DRF Project

## Project Overview
This project is an e-commerce application built using Django and Django REST Framework (DRF) for the backend, with a frontend developed in Next.js. The application allows users to register, manage their profiles, and place orders for products.

## Directory Structure
```
ecommerce-drf
├── apps
│   ├── accounts          # User account management
│   ├── orders            # Order management
│   └── products          # Product management
├── core                  # Core application settings and configurations
├── requirements.txt      # Required Python packages
└── manage.py             # Command-line utility for the project
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd ecommerce-drf
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

- **User Registration and Authentication**
  - `POST /api/accounts/register/` - Register a new user
  - `POST /api/accounts/login/` - Log in a user

- **Product Management**
  - `GET /api/products/` - List all products
  - `GET /api/products/<id>/` - Retrieve a specific product

- **Order Management**
  - `POST /api/orders/` - Create a new order
  - `GET /api/orders/` - List all orders

## Usage
After setting up the project, you can use tools like Postman or cURL to interact with the API endpoints. Make sure to include authentication tokens where required.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.