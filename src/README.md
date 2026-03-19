# Slalom Capabilities Management API

<p align="center">
  <img src="https://colby-timm.github.io/images/byte-teacher.png" alt="Byte Teacher" width="200" />
</p>

A FastAPI application that enables Slalom consultants to register their capabilities and manage consulting expertise across the organization.

## Features

- View all available consulting capabilities
- Submit consultant access requests for practice lead review
- Practice lead sign-in with role-based capability management
- Track skill levels and certifications
- Audit capability changes and approvals

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc
   - Capabilities Dashboard: http://localhost:8000/

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/auth/session`                                                   | Get the current session state                                       |
| POST   | `/auth/login`                                                     | Sign in as a practice lead                                          |
| POST   | `/auth/logout`                                                    | End the current session                                             |
| GET    | `/capabilities`                                                   | Get capabilities, consultants, and pending requests                 |
| POST   | `/capabilities/{capability_name}/request-access`                  | Submit a consultant access request                                  |
| POST   | `/capabilities/{capability_name}/register`                        | Register a consultant directly as a practice lead                   |
| POST   | `/capabilities/{capability_name}/approve-request`                 | Approve a pending consultant request                                |
| DELETE | `/capabilities/{capability_name}/unregister?email=consultant@slalom.com` | Unregister a consultant as a practice lead                  |
| GET    | `/audit-log`                                                      | View recent auditable management activity                           |

## Data Model

The application uses a consulting-focused data model:

1. **Capabilities** - Uses capability name as identifier:
   - Description of the consulting capability
   - Skill levels (Emerging, Proficient, Advanced, Expert)
   - Practice area (Strategy, Technology, Operations)
   - Industry verticals served
   - Required certifications
   - List of consultant emails registered
   - Available capacity (hours per week)
   - Geographic location preferences

2. **Consultants** - Uses email as identifier:
   - Name
   - Practice area
   - Skill level
   - Certifications
   - Availability

All data is currently stored in memory for this learning exercise. In a production environment, this would be backed by a robust database system.

## Demo Practice Lead Accounts

Practice lead credentials live in `src/practice_leads.json` with salted PBKDF2 password hashes.

- Username: `karima.lead`
- Password: `slalom-admin-2026`
- Scope: all practice areas

- Username: `taylor.practice`
- Password: `slalom-tech-2026`
- Scope: Technology only

## Future Enhancements

This exercise will guide you through implementing:
- Capability maturity assessments
- Intelligent team matching algorithms  
- Analytics dashboards for practice leads
- Integration with project management systems
- Advanced search and filtering capabilities
