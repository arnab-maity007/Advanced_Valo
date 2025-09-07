const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const path = require('path');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { PythonShell } = require('python-shell');
const cron = require('node-cron');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// MongoDB connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/valorant_ai', {
  useNewUrlParser: true,
  useUnifiedTopology: true
});

// User Schema
const UserSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  avatar: { type: String, default: '' },
  streamingPlatforms: [{
    platform: String, // twitch, youtube, discord
    username: String,
    connected: Boolean,
    accessToken: String
  }],
  preferences: {
    commentaryStyle: { type: String, default: 'professional' },
    autoStart: { type: Boolean, default: false },
    voiceEnabled: { type: Boolean, default: true }
  },
  createdAt: { type: Date, default: Date.now }
});

// Session Schema
const SessionSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  sessionId: { type: String, required: true },
  startTime: { type: Date, default: Date.now },
  endTime: Date,
  status: { type: String, enum: ['active', 'paused', 'ended'], default: 'active' },
  gameData: {
    map: String,
    agent: String,
    gameMode: String,
    rounds: [{
      roundNumber: Number,
      side: String, // attack/defense
      result: String, // win/loss
      score: String,
      events: [{
        timestamp: Date,
        type: String, // kill, death, assist, spike_plant, etc.
        description: String
      }]
    }]
  },
  commentary: [{
    timestamp: Date,
    text: String,
    confidence: Number,
    type: String // buy_phase, tactical, play_by_play
  }],
  analytics: {
    totalRounds: Number,
    winRate: Number,
    avgKDA: Number,
    commentary_accuracy: Number
  }
});

const User = mongoose.model('User', UserSchema);
const Session = mongoose.model('Session', SessionSchema);

// Authentication middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.sendStatus(401);
  }

  jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key', (err, user) => {
    if (err) return res.sendStatus(403);
    req.user = user;
    next();
  });
};

// Routes
app.post('/api/auth/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    
    const existingUser = await User.findOne({ 
      $or: [{ email }, { username }] 
    });
    
    if (existingUser) {
      return res.status(400).json({ error: 'User already exists' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    const user = new User({
      username,
      email,
      password: hashedPassword
    });

    await user.save();
    
    const token = jwt.sign(
      { userId: user._id, username: user.username },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    );

    res.json({ token, user: { id: user._id, username, email } });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({ error: 'Invalid credentials' });
    }

    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) {
      return res.status(400).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign(
      { userId: user._id, username: user.username },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    );

    res.json({ 
      token, 
      user: { 
        id: user._id, 
        username: user.username, 
        email: user.email,
        preferences: user.preferences
      } 
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Commentary System Routes
app.post('/api/commentary/start', authenticateToken, async (req, res) => {
  try {
    const { gameSettings } = req.body;
    const sessionId = require('uuid').v4();
    
    const session = new Session({
      userId: req.user.userId,
      sessionId,
      gameData: {
        map: gameSettings.map,
        agent: gameSettings.agent,
        gameMode: gameSettings.gameMode
      }
    });
    
    await session.save();
    
    // Start Python commentary script
    const options = {
      mode: 'text',
      pythonOptions: ['-u'],
      scriptPath: path.join(__dirname, '..'),
      args: [sessionId, req.user.userId]
    };
    
    const pyshell = new PythonShell('Output Processed Json/buycommentary.py', options);
    
    pyshell.on('message', (message) => {
      // Emit commentary to client
      io.to(sessionId).emit('commentary', {
        timestamp: new Date(),
        text: message,
        type: 'live_commentary'
      });
    });
    
    res.json({ sessionId, status: 'started' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/commentary/stop/:sessionId', authenticateToken, async (req, res) => {
  try {
    const { sessionId } = req.params;
    
    await Session.findOneAndUpdate(
      { sessionId, userId: req.user.userId },
      { 
        endTime: new Date(),
        status: 'ended'
      }
    );
    
    res.json({ status: 'stopped' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Dashboard Routes
app.get('/api/dashboard/stats', authenticateToken, async (req, res) => {
  try {
    const sessions = await Session.find({ userId: req.user.userId });
    
    const stats = {
      totalSessions: sessions.length,
      totalHours: sessions.reduce((acc, session) => {
        if (session.endTime) {
          return acc + ((session.endTime - session.startTime) / (1000 * 60 * 60));
        }
        return acc;
      }, 0),
      avgAccuracy: sessions.reduce((acc, session) => {
        return acc + (session.analytics?.commentary_accuracy || 0);
      }, 0) / sessions.length || 0,
      recentSessions: sessions.slice(-5).reverse()
    };
    
    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/dashboard/history', authenticateToken, async (req, res) => {
  try {
    const { page = 1, limit = 10 } = req.query;
    
    const sessions = await Session.find({ userId: req.user.userId })
      .sort({ startTime: -1 })
      .limit(limit * 1)
      .skip((page - 1) * limit);
    
    const total = await Session.countDocuments({ userId: req.user.userId });
    
    res.json({
      sessions,
      totalPages: Math.ceil(total / limit),
      currentPage: page
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Streaming Platform Integration
app.post('/api/streaming/connect', authenticateToken, async (req, res) => {
  try {
    const { platform, credentials } = req.body;
    
    // Here you would implement OAuth flows for different platforms
    // For now, we'll simulate the connection
    
    await User.findByIdAndUpdate(req.user.userId, {
      $push: {
        streamingPlatforms: {
          platform,
          username: credentials.username,
          connected: true,
          accessToken: credentials.token || 'simulated-token'
        }
      }
    });
    
    res.json({ status: 'connected', platform });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// WebSocket handling
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);
  
  socket.on('join-session', (sessionId) => {
    socket.join(sessionId);
    console.log(`User joined session: ${sessionId}`);
  });
  
  socket.on('game-event', (data) => {
    // Handle real-time game events
    socket.to(data.sessionId).emit('game-update', data);
  });
  
  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
  });
});

// Serve the main app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`🚀 Valorant AI Commentary Server running on port ${PORT}`);
});
