# Shiganshina Social

Shiganshina Social is a real-time social media application that enables seamless user communication, image sharing, and integration with external social media platforms. Built using TypeScript with React.js on the frontend and Django on the backend, it provides a responsive and interactive user experience with real-time updates without page refreshes.

## Features

- **User Communication**: Seamless messaging and notifications for better connectivity.
- **Image Sharing**: Users can easily upload and share images.
- **Markdown Support**: Custom posts with markdown formatting for rich text and media content.
- **Integration with Social Media**: Supports sharing content to other platforms.
- **Real-Time Updates**: Dynamic data rendering without the need for manual page refreshes.
- **Responsive Design**: Optimized for both desktop and mobile users.

## Tech Stack

### Frontend
- **TypeScript**
- **React.js**
- **CSS/SASS**: For styling and responsive design.

### Backend
- **Django**
- **REST API**: For communication between the frontend and backend.

### Database
- **PostgreSQL**: Reliable and scalable storage solution.

### Deployment
- **Heroku**: Easy deployment and scaling of the application.

## Development Approach

### Agile Methodologies
- The project was developed using Agile practices with regular sprints and task management.
- Ensured collaboration across the team, with frequent stand-ups and code reviews to maintain high standards.

### Test-Driven Development (TDD)
- Comprehensive testing implemented to maintain code quality and ensure robust application functionality.
- **Unit Tests**: Developed using TDD principles to minimize bugs and improve maintainability.

## Installation and Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/devisals/Shiganshina-Social.git
   cd Shiganshina-Social
   ```

2. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Run Frontend:**
   ```bash
   npm start
   ```

4. **Install Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **Run Backend:**
   ```bash
   python manage.py runserver
   ```

6. **Environment Variables:**
   - Create a `.env` file in the root directory and add your environment variables for database connection, social media API keys, and other configurations.

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue for any bug reports or feature requests.

1. Fork the repository.
2. Create your feature branch:
   ```bash
   git checkout -b feature/YourFeatureName
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add some feature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/YourFeatureName
   ```
5. Open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

This README provides an overview, installation steps, and information about contributing, making it user-friendly and informative.
