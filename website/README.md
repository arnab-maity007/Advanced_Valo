# Valorant AI Commentary Web Platform

A modern, responsive web interface for the Valorant AI Commentary system that makes AI-powered game commentary accessible to all streamers.

## 🎮 Features

### Core Functionality
- **Real-time AI Commentary**: Live analysis and commentary of Valorant gameplay
- **OCR Game Detection**: Automatic detection of game state, agents, maps, and buy phases
- **Multiple Commentary Styles**: Professional, casual, educational, and entertaining modes
- **User Dashboard**: Comprehensive analytics and session management

### Streaming Integration
- **Twitch Integration**: Connect and stream with Twitch API
- **YouTube Live**: YouTube streaming platform support
- **Discord Integration**: Discord server connectivity for community engagement
- **Multi-platform Support**: Simultaneous streaming to multiple platforms

### User Experience
- **Valorant-themed UI**: Modern design with authentic Valorant aesthetics
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Real-time Updates**: Live commentary feed and game state updates
- **Session History**: Track and review past streaming sessions
- **Performance Analytics**: Detailed statistics and accuracy metrics

### Technical Features
- **WebSocket Communication**: Real-time bidirectional communication
- **JWT Authentication**: Secure user authentication and session management
- **MongoDB Database**: Scalable data storage and user management
- **Python Bridge**: Seamless integration with existing OCR/AI systems
- **RESTful API**: Well-structured API for all platform interactions

## 🛠️ Technology Stack

### Frontend
- **HTML5** with semantic markup
- **CSS3** with modern features (Grid, Flexbox, Custom Properties)
- **Vanilla JavaScript** with ES6+ features
- **Socket.IO Client** for real-time communication
- **Responsive Design** with mobile-first approach

### Backend
- **Node.js** with Express.js framework
- **Socket.IO** for WebSocket communication
- **MongoDB** with Mongoose ODM
- **JWT** for authentication
- **Python Shell** for AI system integration

### Python Integration
- **Commentary Bridge**: Python script for seamless integration
- **OCR Processing**: EasyOCR for text detection
- **Agent Detection**: AI model for agent recognition
- **Real-time Analysis**: Live game state processing

## 🚀 Quick Start

### Prerequisites
- Node.js (v16.0.0 or higher)
- Python 3.8+
- MongoDB (local or cloud)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/arnab-maity007/Metamorph.git
   cd Metamorph/website
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Install Python dependencies**
   ```bash
   cd ..
   pip install -r requirements.txt
   cd website
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   npm run setup-db
   ```

6. **Start the development server**
   ```bash
   npm run dev
   ```

7. **Start the Python bridge** (in another terminal)
   ```bash
   npm run bridge
   ```

### Access the Application
- Web Interface: http://localhost:3000
- API Documentation: http://localhost:3000/api
- Default Login: demo@example.com / demo123

## 📖 Usage Guide

### For Streamers

1. **Create Account**: Register with your streaming details
2. **Connect Platforms**: Link your Twitch, YouTube, or Discord accounts
3. **Configure Settings**: Choose commentary style and overlay preferences
4. **Start Commentary**: Launch AI commentary for your Valorant stream
5. **Monitor Performance**: Track accuracy and engagement metrics

### For Developers

1. **API Integration**: Use the RESTful API for custom integrations
2. **WebSocket Events**: Real-time data through Socket.IO
3. **Python Extension**: Extend the AI commentary system
4. **Database Queries**: Access user and session data

## 🔧 Configuration

### Environment Variables
```env
# Server
NODE_ENV=development
PORT=3000

# Database
MONGODB_URI=mongodb://localhost:27017/valorant_ai_commentary

# Authentication
JWT_SECRET=your_secret_key
JWT_EXPIRES_IN=7d

# External APIs
TWITCH_CLIENT_ID=your_twitch_client_id
YOUTUBE_API_KEY=your_youtube_api_key
```

### Commentary Styles
- **Professional**: Formal esports commentary
- **Casual**: Friendly streaming commentary
- **Educational**: Teaching-focused analysis
- **Entertaining**: Humor and engagement focused

## 📊 API Documentation

### Authentication Endpoints
```
POST /api/auth/register - User registration
POST /api/auth/login - User login
GET /api/auth/verify - Token verification
POST /api/auth/logout - User logout
```

### Commentary Endpoints
```
POST /api/commentary/start - Start commentary session
POST /api/commentary/stop/:id - Stop commentary session
GET /api/commentary/status - Get current status
```

### Dashboard Endpoints
```
GET /api/dashboard/stats - User statistics
GET /api/dashboard/history - Session history
GET /api/dashboard/analytics - Performance analytics
```

### Streaming Endpoints
```
POST /api/streaming/connect - Connect platform
GET /api/streaming/platforms - Get connected platforms
DELETE /api/streaming/disconnect - Disconnect platform
```

## 🔌 WebSocket Events

### Client to Server
```javascript
socket.emit('start-commentary', { sessionId, gameSettings });
socket.emit('stop-commentary', { sessionId });
socket.emit('join-session', sessionId);
```

### Server to Client
```javascript
socket.on('commentary', data => { /* New commentary */ });
socket.on('game-update', data => { /* Game state update */ });
socket.on('session-ended', data => { /* Session completed */ });
```

## 🎯 Game Integration

### Supported Games
- **Valorant**: Full support with agent detection, map recognition, buy phase analysis

### Detection Capabilities
- **Agents**: All current Valorant agents
- **Maps**: All competitive maps
- **Game Phases**: Buy phase, round start, round end
- **UI Elements**: Score, timer, inventory

### Commentary Features
- **Strategic Analysis**: Tactical commentary on plays
- **Agent-specific Tips**: Character-specific advice
- **Map Callouts**: Location-based commentary
- **Economic Analysis**: Buy phase optimization

## 🛡️ Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt with salt rounds
- **Rate Limiting**: API request rate limiting
- **Input Validation**: Comprehensive input sanitization
- **CORS Protection**: Cross-origin request security
- **Helmet.js**: Security headers and protection

## 📱 Responsive Design

### Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

### Features
- **Mobile Navigation**: Hamburger menu for mobile devices
- **Touch-friendly**: Optimized for touch interactions
- **Adaptive Layout**: Flexible grid system
- **Performance**: Optimized assets and lazy loading

## 🔄 Development Workflow

### Scripts
```bash
npm run dev         # Development server with hot reload
npm run start       # Production server
npm run bridge     # Start Python bridge
npm run setup-db   # Initialize database
npm run test       # Run test suite
npm run lint       # Code linting
```

### File Structure
```
website/
├── public/           # Static assets
│   ├── css/         # Stylesheets
│   ├── js/          # Client-side JavaScript
│   └── images/      # Images and icons
├── models/          # Database models
├── routes/          # API routes
├── middleware/      # Express middleware
├── bridge/          # Python integration
├── scripts/         # Setup and utility scripts
└── server.js        # Main server file
```

## 🚀 Deployment

### Production Setup
1. **Environment**: Set NODE_ENV=production
2. **Database**: Configure production MongoDB
3. **SSL**: Setup HTTPS certificates
4. **Process Manager**: Use PM2 or similar
5. **Reverse Proxy**: Configure Nginx/Apache

### Deployment Platforms
- **Heroku**: Easy deployment with MongoDB Atlas
- **DigitalOcean**: VPS deployment
- **AWS**: EC2 with RDS/DocumentDB
- **Vercel**: Frontend deployment

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Valorant**: Game assets and inspiration
- **Riot Games**: For creating an amazing game
- **Open Source Community**: For the tools and libraries used
- **Streamers**: For feedback and feature requests

## 📞 Support

- **Issues**: GitHub Issues page
- **Documentation**: In-code documentation
- **Community**: Discord server (link in bio)
- **Email**: support@valorantai.com

---

**Made with ❤️ for the Valorant streaming community**
