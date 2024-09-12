# Digital Library System

---

This project is a digital library system built with Django. The system allows library staff to manage books, readers, borrowing processes, and notifications. Readers can search for books, manage their profiles, and create personalized book lists.

---
## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Docker Setup](#docker-setup)
- [Contributing](#contributing)
- [License](#license)

---
## Features

### For Library Staff

- **Book Management**: CRUD operations for books.
- **Reader Management**: Manage reader profiles.
- **Borrowing System**: Track borrowing history, due dates, and returns.
- **User Authentication and Authorization**: Role-based access control.
- **Notifications and Reminders**: Email notifications for due dates and reminders.
- **Reports and Analytics**: Generate reports for book inventory and borrowing statistics.

### For Readers

- **Search and Filter**: Search for books by title, author, genre, etc.
- **Profile Management**: View and update personal profile and borrowing history.
- **Personalized Book Lists**: Create custom book lists like favorites, read later, and read.

---
## Installation

### Prerequisites

- Python 3.8+
- Django 3.2+
- PostgreSQL or any other database supported by Django

### Steps

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/digital-library-system.git
    cd digital-library-system
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use \`venv\\Scripts\\activate\`
    ```

3. **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure the database:**

    Update the \`DATABASES\` setting in \`settings.py\` to match your database configuration.

5. **Run migrations:**

    ```bash
    python manage.py migrate
    ```

6. **Create a superuser:**

    ```bash
    python manage.py createsuperuser
    ```

7. **Start the development server:**

    ```bash
    python manage.py runserver
    ```

---
## Configuration

### Environment Variables

Create a \`.env\` file in the project root and set the following variables:

- \`SECRET_KEY\`: Django secret key.
- \`DEBUG\`: Set to \`True\` for development and \`False\` for production.
- \`DATABASE_URL\`: Database connection URL.

Example \`.env\` file:

```env
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/digital_library
```

### Google Books API

To use the Google Books API for book registration, obtain an API key and add it to your settings.

---
## Usage

### Access the Admin Interface

Navigate to \`/admin\` and log in with the superuser credentials to manage the system.

### Register New Books

Library staff can register new books through the admin interface or a custom view provided in the app.

### Borrow Books

Readers can borrow books by creating borrow requests. Staff can approve or cancel these requests.

### Personalized Book Lists

Readers can create and manage their book lists by navigating to their profile section.

---
## Testing

Run the tests to ensure everything is working correctly:

```bash
python manage.py test
```

---
## Docker Setup

### Directory Structure

```
project-root/
├── builder/
│   ├── Dockerfile
│   └── web_entrypoint.sh
├── apps/
├── manage.py
├── requirements.txt
└── docker-compose.yml
```

### Build and Start the Containers

```sh
docker-compose up --build
```

This command will build the Docker images and start the containers defined in your \`docker-compose.yml\` file.

### Access the Application

- The Django application will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000)
- RabbitMQ management interface will be available at [http://127.0.0.1:15673](http://127.0.0.1:15673)

### Running Management Commands

You can run Django management commands within the Docker container using the following syntax:

```sh
docker-compose run --rm web python manage.py <command>
```

---
## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes.
4. Push your branch and create a pull request.

---
## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.