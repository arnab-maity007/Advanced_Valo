/**
 * Database Setup Script
 * Initializes MongoDB collections and creates default data
 */

const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
require('dotenv').config();

// Import models
const User = require('../models/User');
const StreamingSession = require('../models/StreamingSession');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/valorant_ai_commentary';

async function setupDatabase() {
  try {
    console.log('Connecting to MongoDB...');
    await mongoose.connect(MONGODB_URI);
    console.log('Connected to MongoDB successfully');

    // Clear existing data (optional - remove in production)
    console.log('Clearing existing data...');
    await User.deleteMany({});
    await StreamingSession.deleteMany({});

    // Create default admin user
    console.log('Creating default admin user...');
    const adminPassword = await bcrypt.hash('admin123', 12);
    const adminUser = new User({
      username: 'admin',
      email: 'admin@valorantai.com',
      password: adminPassword,
      role: 'admin',
      preferences: {
        commentaryStyle: 'professional',
        autoStart: false,
        overlayPosition: 'bottom-right',
        theme: 'valorant'
      },
      streamingPlatforms: {
        twitch: {
          connected: false,
          username: '',
          settings: {
            chatIntegration: false,
            webhookUrl: ''
          }
        },
        youtube: {
          connected: false,
          channelId: '',
          settings: {
            liveChat: false,
            webhookUrl: ''
          }
        },
        discord: {
          connected: false,
          serverId: '',
          settings: {
            channelId: '',
            botToken: ''
          }
        }
      }
    });

    await adminUser.save();
    console.log('Admin user created successfully');

    // Create demo user
    console.log('Creating demo user...');
    const demoPassword = await bcrypt.hash('demo123', 12);
    const demoUser = new User({
      username: 'demo_streamer',
      email: 'demo@example.com',
      password: demoPassword,
      role: 'user',
      preferences: {
        commentaryStyle: 'casual',
        autoStart: true,
        overlayPosition: 'top-left',
        theme: 'valorant'
      },
      streamingPlatforms: {
        twitch: {
          connected: true,
          username: 'demo_valorant_streamer',
          settings: {
            chatIntegration: true,
            webhookUrl: 'https://example.com/webhook'
          }
        }
      }
    });

    await demoUser.save();
    console.log('Demo user created successfully');

    // Create sample streaming session
    console.log('Creating sample streaming session...');
    const sampleSession = new StreamingSession({
      userId: demoUser._id,
      startTime: new Date(Date.now() - 3600000), // 1 hour ago
      endTime: new Date(Date.now() - 1800000), // 30 minutes ago
      gameSettings: {
        map: 'Bind',
        agent: 'Jett',
        commentaryStyle: 'casual'
      },
      gameData: {
        map: 'Bind',
        agent: 'Jett',
        phase: 'round',
        round_number: 12,
        score: { team1: 6, team2: 5 }
      },
      analytics: {
        commentary_count: 45,
        commentary_accuracy: 87.5,
        game_events_detected: 23,
        average_response_time: 1.2
      },
      status: 'completed'
    });

    await sampleSession.save();
    console.log('Sample session created successfully');

    // Create indexes for better performance
    console.log('Creating database indexes...');
    
    // User indexes
    await User.collection.createIndex({ email: 1 }, { unique: true });
    await User.collection.createIndex({ username: 1 }, { unique: true });
    
    // Session indexes
    await StreamingSession.collection.createIndex({ userId: 1 });
    await StreamingSession.collection.createIndex({ startTime: -1 });
    await StreamingSession.collection.createIndex({ status: 1 });
    
    console.log('Indexes created successfully');

    // Display summary
    console.log('\n=== Database Setup Complete ===');
    console.log(`Database: ${MONGODB_URI}`);
    console.log('Collections created:');
    console.log('- users');
    console.log('- streamingsessions');
    console.log('\nDefault accounts created:');
    console.log('- Admin: admin@valorantai.com / admin123');
    console.log('- Demo: demo@example.com / demo123');
    console.log('\nSample data:');
    console.log('- 1 sample streaming session');
    console.log('- Performance indexes created');

    process.exit(0);

  } catch (error) {
    console.error('Database setup failed:', error);
    process.exit(1);
  }
}

// Run setup if called directly
if (require.main === module) {
  setupDatabase();
}

module.exports = { setupDatabase };
