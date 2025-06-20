# Mental Health AI Chatbot

> **HIPAA-Compliant AI Chatbot for Mental Health Therapists**
> 
> Built on GoHighLevel foundation with PydanticAI + DSPy optimization
> 
> **Key Feature**: Therapists never need to see or use GoHighLevel directly

## 🎯 Project Overview

This project creates a sophisticated mental health AI chatbot that:

- **For Therapists**: Provides a clean, therapy-focused interface without CRM complexity
- **For Patients**: Offers 24/7 AI support between therapy sessions with crisis detection
- **For Compliance**: Implements full HIPAA compliance with encryption and audit logging
- **For Integration**: Uses GoHighLevel as the backend foundation while hiding its complexity

## 🏗️ Architecture

```
Patient Interface (Web/Mobile)
        ↓
AI Chatbot (PydanticAI + DSPy)
        ↓
Therapist Dashboard (Therapy-Focused)
        ↓
Security & Compliance Layer (HIPAA)
        ↓
GoHighLevel MCP Integration (Hidden)
        ↓
GoHighLevel Backend (CRM/Communications)
```

## 🔧 Technology Stack

### Core AI Framework
- **PydanticAI**: Type-safe AI agent framework
- **DSPy**: Self-optimizing prompt engineering
- **Instructor**: Structured LLM outputs
- **Marvin**: Complex workflow orchestration

### Backend Infrastructure
- **FastAPI**: High-performance web framework
- **PostgreSQL**: Encrypted patient data storage
- **Redis**: Session management and caching
- **GoHighLevel MCP**: Backend CRM integration

### Security & Compliance
- **AES-256 Encryption**: All patient data encrypted at rest
- **JWT Authentication**: Secure therapist access
- **HIPAA Audit Logging**: Full compliance tracking
- **Crisis Detection**: Real-time risk assessment

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd mental-health-chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -e .
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required Environment Variables:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/mental_health_chatbot
DATABASE_ENCRYPTION_KEY=your-32-byte-base64-key

# GoHighLevel MCP
GHL_API_KEY=your-ghl-private-integrations-api-key
GHL_LOCATION_ID=your-ghl-location-id

# AI Models
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Security
SECRET_KEY=your-super-secret-jwt-key
PATIENT_DATA_ENCRYPTION_KEY=your-patient-encryption-key
```

### 3. Database Setup

```bash
# Run database migrations
alembic upgrade head

# Create initial therapist account
python -m src.scripts.create_therapist --email therapist@example.com
```

### 4. Start the Application

```bash
# Development mode
uvicorn src.main:app --reload --port 8000

# Production mode
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📋 API Endpoints

### Therapist Interface
```
GET  /therapist/dashboard          # Therapy-focused dashboard
GET  /therapist/patients           # Anonymized patient list
POST /therapist/patients/{id}/message  # Send patient message
GET  /therapist/patients/{id}/conversation  # AI conversation review
POST /therapist/patients/{id}/session-note  # Add session notes
GET  /therapist/interface-info     # What therapists see vs. hidden
```

### Patient Chatbot
```
POST /chat/message                 # Send message to AI
GET  /chat/emergency-resources     # Crisis support resources
GET  /chat/session-info           # Current session information
POST /chat/consent                # Provide HIPAA consent
GET  /chat/conversation-history   # Recent chat history
```

### System Health
```
GET  /health                      # Basic health check
GET  /health/detailed            # Detailed system status
```

## 🔒 Security Features

### HIPAA Compliance
- **Encryption**: All patient data encrypted with AES-256
- **Audit Logging**: Every data access logged with timestamps
- **Access Controls**: Role-based permissions for therapists
- **Data Retention**: Configurable retention policies (default: 7 years)
- **Consent Management**: Digital consent tracking

### Crisis Detection
- **Real-time Monitoring**: AI scans for suicide/self-harm indicators
- **Automatic Escalation**: Immediate therapist notification
- **Resource Provision**: 24/7 crisis hotline information
- **Safety Protocols**: Built-in emergency response procedures

### Data Anonymization
- **Patient IDs**: Cryptographically anonymized identifiers
- **Display Names**: Only initials shown to therapists
- **Conversation Data**: Encrypted before storage
- **Audit Trails**: Full compliance documentation

## 🎭 What Therapists See vs. Hidden

### ✅ Therapist Interface (Visible)
- Clean, therapy-focused dashboard
- Anonymized patient summaries (initials only)
- AI conversation insights and summaries
- Crisis alerts and risk assessments
- Session scheduling and documentation
- Therapeutic communication tools

### 🚫 Hidden from Therapists (GHL Complexity)
- CRM pipelines and lead management
- Marketing campaign tools
- Sales analytics and conversion metrics
- Payment processing details
- Business development features
- Complex GoHighLevel configuration

## 🧠 AI Features

### Mental Health Specialization
- **Crisis Detection**: Identifies suicide/self-harm indicators
- **Therapeutic Responses**: Uses evidence-based techniques
- **Risk Assessment**: Continuous monitoring and escalation
- **Session Summaries**: Automated clinical documentation
- **Safety Planning**: Crisis intervention protocols

### DSPy Optimization
- **Prompt Engineering**: Self-improving therapeutic responses
- **Context Awareness**: Maintains conversation continuity
- **Risk Calibration**: Learns from therapist feedback
- **Response Quality**: Continuous optimization

## 📊 Monitoring & Analytics

### For Therapists
- Patient engagement metrics
- Crisis intervention statistics
- Session outcome tracking
- AI conversation summaries

### For Administrators
- System health monitoring
- HIPAA compliance reports
- Performance analytics
- Security audit logs

## 🔧 Development

### Project Structure
```
src/
├── core/           # Configuration and security
├── models/         # Database and API models
├── ai/            # Mental health AI agent
├── ghl/           # GoHighLevel MCP integration
├── api/           # FastAPI routes
└── main.py        # Application entry point
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run HIPAA compliance tests
pytest -m hipaa
```

### Code Quality
```bash
# Format code
black src/

# Lint code
ruff src/

# Type checking
mypy src/
```

## 🚀 Deployment

### Docker
```bash
# Build image
docker build -t mental-health-chatbot .

# Run container
docker run -p 8000:8000 --env-file .env mental-health-chatbot
```

### Cloud Platforms
- **Railway**: `railway up`
- **Vercel**: `vercel deploy`
- **Heroku**: `git push heroku main`
- **AWS/GCP**: Use provided Terraform configs

## 📈 Scaling Considerations

### Performance
- **Database**: Use read replicas for high load
- **Caching**: Redis for session and conversation data
- **AI Models**: Load balancing across multiple providers
- **CDN**: Static asset delivery optimization

### Security
- **WAF**: Web Application Firewall for production
- **VPN**: Secure therapist access
- **Monitoring**: Real-time security alerts
- **Backups**: Encrypted automated backups

## 🆘 Crisis Protocols

### Automatic Detection
- Suicide ideation keywords
- Self-harm language patterns
- Crisis emotional indicators
- Psychosis warning signs

### Response Actions
1. Immediate crisis resources provided to patient
2. Therapist notification (SMS/email/app push)
3. Conversation flagged for urgent review
4. Safety planning resources activated
5. Optional emergency contact notification

## 📞 Support & Resources

### Crisis Resources (Built-in)
- **988 Suicide & Crisis Lifeline**: Call or text 988
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911 for immediate danger

### Technical Support
- Documentation: `/docs` (development mode)
- Health Check: `/health/detailed`
- Logs: Structured logging with Loguru
- Monitoring: Built-in health monitoring

## 📄 License & Compliance

- **HIPAA Compliant**: Full healthcare data protection
- **SOC 2 Ready**: Security and availability controls
- **GDPR Compatible**: Privacy by design principles
- **State Licensing**: Supports all US state therapy licenses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure HIPAA compliance
5. Submit pull request

**Note**: All contributions must maintain HIPAA compliance and cannot compromise patient data security.

---

**⚡ Built with the cutting-edge AI scaffolding strategy discussed earlier**

This implementation demonstrates the genius-level scaffolding approach:
- PydanticAI + DSPy for self-optimizing AI
- Complete GoHighLevel abstraction for therapists
- HIPAA compliance built-in from day one
- Crisis detection and safety protocols
- Natural language development workflows
- Predictive optimization capabilities

The result: Therapists get a clean, therapy-focused interface while patients receive sophisticated AI support, all powered by GoHighLevel's robust backend without the complexity.