class ValorantAI {
  constructor() {
    this.socket = null;
    this.currentSession = null;
    this.isAuthenticated = false;
    this.user = null;
    this.commentaryActive = false;
    
    this.init();
  }

  init() {
    this.bindEvents();
    this.checkAuth();
    this.initSocket();
    this.loadDashboardData();
    
    // Initialize particles effect
    this.initParticles();
  }

  bindEvents() {
    // Navigation
    this.bindNavigation();
    
    // Authentication
    this.bindAuth();
    
    // Commentary controls
    this.bindCommentaryControls();
    
    // Streaming platform connections
    this.bindStreamingPlatforms();
    
    // Modal controls
    this.bindModals();
    
    // Responsive menu
    this.bindResponsiveMenu();
  }

  bindNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = link.getAttribute('href');
        
        // Update active state
        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        // Show/hide sections
        this.showSection(target.substring(1));
      });
    });
  }

  bindAuth() {
    // Login button
    document.getElementById('loginBtn')?.addEventListener('click', () => {
      this.showModal('loginModal');
    });

    // Register button
    document.getElementById('registerBtn')?.addEventListener('click', () => {
      this.showModal('registerModal');
    });

    // Login form
    document.getElementById('loginForm')?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleLogin(e.target);
    });

    // Register form
    document.getElementById('registerForm')?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleRegister(e.target);
    });

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', () => {
      this.handleLogout();
    });

    // Modal switches
    document.getElementById('switchToRegister')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.hideModal('loginModal');
      this.showModal('registerModal');
    });

    document.getElementById('switchToLogin')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.hideModal('registerModal');
      this.showModal('loginModal');
    });
  }

  bindCommentaryControls() {
    // Start commentary button (hero section)
    document.getElementById('startCommentaryBtn')?.addEventListener('click', () => {
      if (!this.isAuthenticated) {
        this.showModal('loginModal');
        return;
      }
      this.showSection('dashboard');
    });

    // Dashboard commentary controls
    document.getElementById('startBtn')?.addEventListener('click', () => {
      this.startCommentary();
    });

    document.getElementById('pauseBtn')?.addEventListener('click', () => {
      this.pauseCommentary();
    });

    document.getElementById('stopBtn')?.addEventListener('click', () => {
      this.stopCommentary();
    });

    // Quick start button
    document.getElementById('quickStartBtn')?.addEventListener('click', () => {
      this.quickStartCommentary();
    });

    // Toggle commentary overlay
    document.getElementById('toggleOverlay')?.addEventListener('click', () => {
      this.toggleCommentaryOverlay();
    });
  }

  bindStreamingPlatforms() {
    const platformButtons = document.querySelectorAll('.btn-platform');
    platformButtons.forEach(button => {
      button.addEventListener('click', () => {
        const platform = button.getAttribute('data-platform');
        this.connectStreamingPlatform(platform);
      });
    });
  }

  bindModals() {
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(button => {
      button.addEventListener('click', () => {
        const modalId = button.getAttribute('data-modal');
        this.hideModal(modalId);
      });
    });

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal')) {
        this.hideModal(e.target.id);
      }
    });
  }

  bindResponsiveMenu() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    
    hamburger?.addEventListener('click', () => {
      navMenu.classList.toggle('active');
    });
  }

  initSocket() {
    if (typeof io !== 'undefined') {
      this.socket = io();
      
      this.socket.on('connect', () => {
        console.log('Connected to server');
      });

      this.socket.on('commentary', (data) => {
        this.handleCommentaryUpdate(data);
      });

      this.socket.on('game-update', (data) => {
        this.handleGameUpdate(data);
      });

      this.socket.on('disconnect', () => {
        console.log('Disconnected from server');
      });
    }
  }

  initParticles() {
    // Add dynamic particle effects to hero section
    const heroParticles = document.querySelector('.hero-particles');
    if (heroParticles) {
      // Particle animation is handled by CSS
      // This could be enhanced with canvas or WebGL for more complex effects
    }
  }

  checkAuth() {
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Verify token with server
      this.verifyToken(token);
    }
  }

  async verifyToken(token) {
    try {
      const response = await fetch('/api/auth/verify', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        this.setAuthenticatedUser(userData.user);
      } else {
        localStorage.removeItem('auth_token');
      }
    } catch (error) {
      console.error('Token verification failed:', error);
      localStorage.removeItem('auth_token');
    }
  }

  async handleLogin(form) {
    const formData = new FormData(form);
    const email = formData.get('email') || document.getElementById('loginEmail').value;
    const password = formData.get('password') || document.getElementById('loginPassword').value;

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('auth_token', data.token);
        this.setAuthenticatedUser(data.user);
        this.hideModal('loginModal');
        this.showNotification('Login successful!', 'success');
        this.loadDashboardData();
      } else {
        this.showNotification(data.error || 'Login failed', 'error');
      }
    } catch (error) {
      console.error('Login error:', error);
      this.showNotification('Login failed. Please try again.', 'error');
    }
  }

  async handleRegister(form) {
    const formData = new FormData(form);
    const username = formData.get('username') || document.getElementById('registerUsername').value;
    const email = formData.get('email') || document.getElementById('registerEmail').value;
    const password = formData.get('password') || document.getElementById('registerPassword').value;
    const confirmPassword = formData.get('confirmPassword') || document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
      this.showNotification('Passwords do not match', 'error');
      return;
    }

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('auth_token', data.token);
        this.setAuthenticatedUser(data.user);
        this.hideModal('registerModal');
        this.showNotification('Registration successful!', 'success');
        this.loadDashboardData();
      } else {
        this.showNotification(data.error || 'Registration failed', 'error');
      }
    } catch (error) {
      console.error('Registration error:', error);
      this.showNotification('Registration failed. Please try again.', 'error');
    }
  }

  handleLogout() {
    localStorage.removeItem('auth_token');
    this.isAuthenticated = false;
    this.user = null;
    this.updateAuthUI();
    this.showSection('home');
    this.showNotification('Logged out successfully', 'success');
  }

  setAuthenticatedUser(user) {
    this.isAuthenticated = true;
    this.user = user;
    this.updateAuthUI();
  }

  updateAuthUI() {
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const userMenu = document.getElementById('userMenu');
    const username = document.getElementById('username');

    if (this.isAuthenticated) {
      loginBtn.style.display = 'none';
      registerBtn.style.display = 'none';
      userMenu.style.display = 'flex';
      username.textContent = this.user.username;
    } else {
      loginBtn.style.display = 'inline-flex';
      registerBtn.style.display = 'inline-flex';
      userMenu.style.display = 'none';
    }
  }

  async loadDashboardData() {
    if (!this.isAuthenticated) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/dashboard/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const stats = await response.json();
        this.updateDashboardStats(stats);
        this.loadRecentSessions();
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  }

  updateDashboardStats(stats) {
    document.getElementById('totalHours').textContent = Math.round(stats.totalHours || 0);
    document.getElementById('totalSessions').textContent = stats.totalSessions || 0;
    document.getElementById('avgAccuracy').textContent = `${Math.round(stats.avgAccuracy || 0)}%`;
    // Viewer count would come from streaming platform APIs
    document.getElementById('viewerCount').textContent = Math.floor(Math.random() * 1000); // Simulated
  }

  async loadRecentSessions() {
    if (!this.isAuthenticated) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/dashboard/history?limit=5', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        this.updateSessionsTable(data.sessions);
      }
    } catch (error) {
      console.error('Failed to load recent sessions:', error);
    }
  }

  updateSessionsTable(sessions) {
    const tbody = document.getElementById('sessionsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    sessions.forEach(session => {
      const row = document.createElement('tr');
      const startTime = new Date(session.startTime);
      const duration = session.endTime ? 
        Math.round((new Date(session.endTime) - startTime) / (1000 * 60)) : 
        'Ongoing';

      row.innerHTML = `
        <td>${startTime.toLocaleDateString()}</td>
        <td>${duration === 'Ongoing' ? duration : `${duration}m`}</td>
        <td>${session.gameData?.map || 'Auto-detect'}</td>
        <td>${session.gameData?.agent || 'Auto-detect'}</td>
        <td>${Math.round(session.analytics?.commentary_accuracy || 0)}%</td>
        <td>
          <button class="btn btn-small btn-outline" onclick="app.viewSession('${session._id}')">
            <i class="fas fa-eye"></i> View
          </button>
        </td>
      `;
      tbody.appendChild(row);
    });
  }

  async startCommentary() {
    if (!this.isAuthenticated) {
      this.showNotification('Please login to start commentary', 'error');
      return;
    }

    const gameSettings = {
      map: document.getElementById('mapSelect')?.value || '',
      agent: document.getElementById('agentSelect')?.value || '',
      commentaryStyle: document.getElementById('commentaryStyle')?.value || 'professional'
    };

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/commentary/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ gameSettings })
      });

      if (response.ok) {
        const data = await response.json();
        this.currentSession = data.sessionId;
        this.commentaryActive = true;
        this.updateCommentaryStatus('Active');
        this.updateCommentaryControls();
        this.showCommentaryOverlay();
        
        // Join socket room for this session
        if (this.socket) {
          this.socket.emit('join-session', this.currentSession);
        }

        this.showNotification('Commentary started successfully!', 'success');
      } else {
        const error = await response.json();
        this.showNotification(error.error || 'Failed to start commentary', 'error');
      }
    } catch (error) {
      console.error('Failed to start commentary:', error);
      this.showNotification('Failed to start commentary', 'error');
    }
  }

  async pauseCommentary() {
    if (!this.currentSession) return;

    this.commentaryActive = false;
    this.updateCommentaryStatus('Paused');
    this.updateCommentaryControls();
    this.showNotification('Commentary paused', 'info');
  }

  async stopCommentary() {
    if (!this.currentSession) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/commentary/stop/${this.currentSession}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        this.currentSession = null;
        this.commentaryActive = false;
        this.updateCommentaryStatus('Ready');
        this.updateCommentaryControls();
        this.hideCommentaryOverlay();
        this.loadDashboardData(); // Refresh stats
        this.showNotification('Commentary stopped', 'info');
      }
    } catch (error) {
      console.error('Failed to stop commentary:', error);
    }
  }

  quickStartCommentary() {
    // Set default values and start immediately
    document.getElementById('mapSelect').value = '';
    document.getElementById('agentSelect').value = '';
    document.getElementById('commentaryStyle').value = 'professional';
    
    this.startCommentary();
  }

  updateCommentaryStatus(status) {
    const statusText = document.querySelector('.status-text');
    const statusDot = document.querySelector('.status-dot');
    
    if (statusText) statusText.textContent = status;
    if (statusDot) {
      statusDot.className = 'status-dot';
      if (status === 'Active') {
        statusDot.classList.add('status-active');
      } else if (status === 'Paused') {
        statusDot.classList.add('status-paused');
      }
    }
  }

  updateCommentaryControls() {
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const stopBtn = document.getElementById('stopBtn');

    if (this.commentaryActive) {
      startBtn.disabled = true;
      pauseBtn.disabled = false;
      stopBtn.disabled = false;
    } else if (this.currentSession) {
      startBtn.disabled = true;
      pauseBtn.disabled = true;
      stopBtn.disabled = false;
    } else {
      startBtn.disabled = false;
      pauseBtn.disabled = true;
      stopBtn.disabled = true;
    }
  }

  handleCommentaryUpdate(data) {
    this.addCommentaryItem(data);
  }

  handleGameUpdate(data) {
    // Handle real-time game updates
    console.log('Game update:', data);
  }

  addCommentaryItem(commentary) {
    const feed = document.getElementById('commentaryFeed');
    if (!feed) return;

    const item = document.createElement('div');
    item.className = 'commentary-item';
    item.innerHTML = `
      <div class="commentary-timestamp">${new Date(commentary.timestamp).toLocaleTimeString()}</div>
      <div class="commentary-text">${commentary.text}</div>
    `;

    feed.appendChild(item);
    feed.scrollTop = feed.scrollHeight;

    // Limit number of items to prevent memory issues
    const items = feed.querySelectorAll('.commentary-item');
    if (items.length > 50) {
      items[0].remove();
    }
  }

  showCommentaryOverlay() {
    const overlay = document.getElementById('commentaryOverlay');
    if (overlay) {
      overlay.style.display = 'block';
    }
  }

  hideCommentaryOverlay() {
    const overlay = document.getElementById('commentaryOverlay');
    if (overlay) {
      overlay.style.display = 'none';
    }
  }

  toggleCommentaryOverlay() {
    const overlay = document.getElementById('commentaryOverlay');
    if (overlay) {
      overlay.style.display = overlay.style.display === 'none' ? 'block' : 'none';
    }
  }

  async connectStreamingPlatform(platform) {
    if (!this.isAuthenticated) {
      this.showNotification('Please login to connect streaming platforms', 'error');
      return;
    }

    try {
      // This would typically open OAuth flow
      // For now, we'll simulate the connection
      const credentials = {
        username: prompt(`Enter your ${platform} username:`),
        token: 'simulated-token'
      };

      if (!credentials.username) return;

      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/streaming/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ platform, credentials })
      });

      if (response.ok) {
        this.showNotification(`${platform} connected successfully!`, 'success');
      } else {
        const error = await response.json();
        this.showNotification(error.error || 'Connection failed', 'error');
      }
    } catch (error) {
      console.error('Failed to connect platform:', error);
      this.showNotification('Connection failed', 'error');
    }
  }

  showSection(sectionId) {
    // Hide all sections
    const sections = ['home', 'features', 'dashboard', 'streaming'];
    sections.forEach(id => {
      const element = document.getElementById(id);
      if (element) {
        if (id === sectionId) {
          element.style.display = 'block';
        } else {
          element.style.display = id === 'home' ? 'flex' : 'none';
        }
      }
    });

    // Special handling for dashboard - only show if authenticated
    if (sectionId === 'dashboard' && !this.isAuthenticated) {
      this.showModal('loginModal');
      return;
    }

    // Smooth scroll to section
    const targetElement = document.getElementById(sectionId);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth' });
    }
  }

  showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.style.display = 'block';
      // Focus first input
      const firstInput = modal.querySelector('input');
      if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
      }
    }
  }

  hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.style.display = 'none';
      // Clear form inputs
      const form = modal.querySelector('form');
      if (form) {
        form.reset();
      }
    }
  }

  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <i class="fas fa-${this.getNotificationIcon(type)}"></i>
        <span>${message}</span>
        <button class="notification-close">&times;</button>
      </div>
    `;

    // Add styles
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: var(--spacing-md);
      box-shadow: var(--shadow-lg);
      z-index: 10001;
      animation: slideInRight 0.3s ease;
      max-width: 300px;
    `;

    // Add to DOM
    document.body.appendChild(notification);

    // Bind close button
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
      this.hideNotification(notification);
    });

    // Auto-hide after 5 seconds
    setTimeout(() => {
      this.hideNotification(notification);
    }, 5000);
  }

  hideNotification(notification) {
    notification.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }

  getNotificationIcon(type) {
    const icons = {
      success: 'check-circle',
      error: 'exclamation-circle',
      warning: 'exclamation-triangle',
      info: 'info-circle'
    };
    return icons[type] || 'info-circle';
  }

  viewSession(sessionId) {
    // This would open a detailed view of the session
    console.log('Viewing session:', sessionId);
    this.showNotification('Session details coming soon!', 'info');
  }
}

// Add notification animations to CSS
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
  @keyframes slideInRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideOutRight {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }

  .notification-content {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    color: var(--text-primary);
  }

  .notification-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1.2rem;
    margin-left: auto;
  }

  .notification-close:hover {
    color: var(--text-primary);
  }

  .notification-success {
    border-left: 4px solid var(--accent-green);
  }

  .notification-error {
    border-left: 4px solid var(--primary-red);
  }

  .notification-warning {
    border-left: 4px solid var(--accent-gold);
  }

  .notification-info {
    border-left: 4px solid var(--accent-cyan);
  }

  .status-active {
    background: var(--accent-green) !important;
  }

  .status-paused {
    background: var(--accent-gold) !important;
  }
`;
document.head.appendChild(notificationStyles);

// Initialize the application
const app = new ValorantAI();

// Export for global access
window.app = app;
