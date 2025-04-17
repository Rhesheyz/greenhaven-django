# Green Haven
## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
## Introduction
Green Haven is a backend project built with Django, designed to provide a robust and scalable backend for managing various functionalities. Its goal is to offer an efficient solution with RESTful API support for seamless integration.
## Features
- **Developed with Django**: Utilizing the Django framework for rapid development and clean design.
- **RESTful API Support**: Enables easy integration with front-end applications.
- **User Authentication and Authorization**: Secure access with built-in authentication.
- **Admin Dashboard**: Powerful admin interface for managing data.
- **Database Integration**: Supports relational databases for robust data management.
- **AI Chatbot Integration**: Powered by Gemini, offering intelligent and conversational support.
- **Content Management**: Tools for managing and organizing content efficiently.
- **Analytics Middleware**: Middleware to track application performance and user interactions.
- **Custom Event Analytics**: Define and monitor specific user events.
- **Compliance Log Analytics**: Ensure adherence to regulations with detailed logging and tracking.
- **AI Usage Analytics**: Monitor and optimize AI feature utilization.
- **AI Feedback Analytics**: Collect and analyze feedback related to AI interactions.
## Installation
Follow these steps to set up the project:
1. **Clone the Repository**
   ```bash
   git clone https://github.com/FchDxCode/Green-Haven.git
   cd Green-Haven
   ```
2. **Create and Activate a Virtual Environment**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
3. **Install the Required Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Apply Migrations**
   - Create migrations:
     ```bash
     python manage.py makemigrations
     ```
   - Apply migrations:
     ```bash
     python manage.py migrate
     ```
5. **Collect Static Files**
   ```bash
   python manage.py collectstatic
   ```
6. **Start the Development Server**
   ```bash
   python manage.py runserver
   ```
## Usage
Once the development server is running, you can:
- Access the API endpoints at `http://127.0.0.1:8000/`.
- Use the admin panel at `http://127.0.0.1:8000/admin` for managing the backend.
## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Make your changes and commit them:
   ```bash
   git commit -m "Add a new feature"
   ```
4. Push to your fork:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.
## Deployment
You can access the deployed application at [Green Haven](https://greenhaven.aisma.co.id).
## License
This project is proprietary and strictly intended for use in the competition. Redistribution, modification, or commercial use without explicit permission from the author is prohibited.
