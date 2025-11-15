// Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global state
let currentSessionId = null;
let currentPredictions = [];
let uploadedFile = null;
let dailyChart = null;
let foodsChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeUpload();
    setupDragAndDrop();
});

// Initialize upload functionality
function initializeUpload() {
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');

    fileInput.addEventListener('change', handleFileSelect);
    uploadArea.addEventListener('click', () => fileInput.click());
}

// Setup drag and drop
function setupDragAndDrop() {
    const uploadArea = document.getElementById('upload-area');

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// Handle file processing
function handleFile(file) {
    // Validate file type
    if (!file.type.match('image.*')) {
        showError('Please upload an image file (PNG, JPG, or GIF)');
        return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('File size must be less than 10MB');
        return;
    }

    uploadedFile = file;
    uploadImage(file);
}

// Upload image to API
async function uploadImage(file) {
    showSection('loading-section');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/predict/top3`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        handlePredictionResult(result);

    } catch (error) {
        console.error('Upload error:', error);
        showError('Failed to analyze image. Please make sure the backend server is running.');
    }
}

// Handle prediction result
function handlePredictionResult(result) {
    currentSessionId = result.session_id;
    currentPredictions = result.top_predictions;

    if (result.is_confident) {
        showHighConfidenceResult(result);
    } else {
        showLowConfidenceResult(result);
    }
}

// Show high confidence result
function showHighConfidenceResult(result) {
    const topPrediction = result.top_predictions[0];

    // Update UI
    document.getElementById('detected-food-name').textContent = topPrediction.label;
    document.getElementById('confidence-percent').textContent = `${topPrediction.confidence_percent}%`;
    document.getElementById('confidence-fill').style.width = `${topPrediction.confidence_percent}%`;
    
    document.getElementById('high-calories').textContent = topPrediction.calories;
    document.getElementById('high-protein').textContent = `${topPrediction.protein}g`;
    document.getElementById('high-fats').textContent = `${topPrediction.fats}g`;

    showSection('high-confidence-section');
}

// Show low confidence result
function showLowConfidenceResult(result) {
    document.getElementById('low-confidence-message').textContent = result.message;

    const optionsList = document.getElementById('options-list');
    optionsList.innerHTML = '';

    result.top_predictions.forEach((prediction, index) => {
        const optionCard = createOptionCard(prediction, index + 1);
        optionsList.appendChild(optionCard);
    });

    showSection('low-confidence-section');
}

// Create option card
function createOptionCard(prediction, optionNumber) {
    const card = document.createElement('div');
    card.className = 'option-card';
    card.onclick = () => selectOption(optionNumber, card);

    card.innerHTML = `
        <div class="option-info">
            <div class="option-name">${prediction.label}</div>
            <div class="option-confidence">Confidence: ${prediction.confidence_percent}%</div>
        </div>
        <div class="option-nutrition">
            <div class="option-nutrition-item">
                <div class="option-nutrition-value">${prediction.calories}</div>
                <div class="option-nutrition-label">Calories</div>
            </div>
            <div class="option-nutrition-item">
                <div class="option-nutrition-value">${prediction.protein}g</div>
                <div class="option-nutrition-label">Protein</div>
            </div>
            <div class="option-nutrition-item">
                <div class="option-nutrition-value">${prediction.fats}g</div>
                <div class="option-nutrition-label">Fats</div>
            </div>
        </div>
    `;

    return card;
}

// Select option from low confidence results
function selectOption(optionNumber, cardElement) {
    // Remove selected class from all cards
    document.querySelectorAll('.option-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Add selected class to clicked card
    cardElement.classList.add('selected');

    // Confirm selection after a short delay
    setTimeout(() => {
        confirmSelection(optionNumber);
    }, 300);
}

// Show alternatives (from high confidence view)
function showAlternatives() {
    const result = {
        top_predictions: currentPredictions,
        message: 'Please select from the alternatives below:'
    };
    showLowConfidenceResult(result);
}

// Confirm selection
async function confirmSelection(selectedOption) {
    showSection('loading-section');

    const selectedPrediction = currentPredictions[selectedOption - 1];

    try {
        const response = await fetch(`${API_BASE_URL}/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                selected_option: selectedOption,
                notes: `Selected option ${selectedOption}`
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        showSuccessResult(selectedPrediction.label, result.nutritional_info || selectedPrediction);

    } catch (error) {
        console.error('Confirmation error:', error);
        showError('Failed to log your selection. Please try again.');
    }
}

// Show manual entry
function showManualEntry() {
    document.getElementById('food-name-input').value = '';
    document.getElementById('portion-size').value = '1';
    document.getElementById('notes-input').value = '';
    showSection('manual-entry-section');
}

// Submit custom entry
async function submitCustomEntry() {
    const foodName = document.getElementById('food-name-input').value.trim();
    const portionSize = parseFloat(document.getElementById('portion-size').value) || 1.0;
    const notes = document.getElementById('notes-input').value.trim();

    if (!foodName) {
        alert('Please enter a food name');
        return;
    }

    showSection('loading-section');

    try {
        const response = await fetch(`${API_BASE_URL}/custom-entry`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId || generateSessionId(),
                food_name: foodName,
                quantity: portionSize,
                notes: notes || undefined
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        showSuccessResult(result.food_name, result.nutritional_info);

    } catch (error) {
        console.error('Custom entry error:', error);
        showError('Failed to submit your entry. Please try again.');
    }
}

// Go back to options
function goBackToOptions() {
    if (currentPredictions && currentPredictions.length > 0) {
        const result = {
            top_predictions: currentPredictions,
            message: 'Please select from the options below:'
        };
        showLowConfidenceResult(result);
    } else {
        showSection('upload-section');
    }
}

// Show success result
function showSuccessResult(foodName, nutritionalInfo) {
    document.getElementById('final-food-name').textContent = foodName;
    document.getElementById('final-calories').textContent = nutritionalInfo.calories || 0;
    document.getElementById('final-protein').textContent = `${nutritionalInfo.protein || 0}g`;
    document.getElementById('final-fats').textContent = `${nutritionalInfo.fats || 0}g`;

    showSection('success-section');
}

// Show error
function showError(message) {
    document.getElementById('error-message').textContent = message;
    showSection('error-section');
}

// Show section
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    // Show selected section
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.add('active');
    }
}

// Reset app
function resetApp() {
    currentSessionId = null;
    currentPredictions = [];
    uploadedFile = null;
    
    // Reset file input
    document.getElementById('file-input').value = '';
    
    showSection('upload-section');
}

// Tab navigation
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Find and activate the clicked tab
    const clickedTab = event?.target || document.querySelector(`[onclick*="${tabName}"]`);
    if (clickedTab) {
        clickedTab.classList.add('active');
    }

    // Hide all tab content
    document.getElementById('home-tab-content').style.display = 'none';
    document.getElementById('dashboard-tab-content').style.display = 'none';

    // Show selected tab
    if (tabName === 'home') {
        document.getElementById('home-tab-content').style.display = 'block';
    } else if (tabName === 'dashboard') {
        document.getElementById('dashboard-tab-content').style.display = 'block';
        loadDashboard();
    }
}

// Load dashboard data
async function loadDashboard() {
    try {
        // Fetch statistics
        const statsResponse = await fetch(`${API_BASE_URL}/logs/statistics`);
        const stats = await statsResponse.json();
        
        // Update stats cards
        document.getElementById('total-meals').textContent = stats.total_predictions || 0;
        document.getElementById('total-calories').textContent = Math.round(stats.total_calories || 0);
        document.getElementById('avg-calories').textContent = Math.round(stats.average_calories || 0);
        document.getElementById('accuracy-rate').textContent = `${Math.round(stats.accuracy_rate || 0)}%`;

        // Fetch trends
        const trendsResponse = await fetch(`${API_BASE_URL}/logs/trends?days=7`);
        const trends = await trendsResponse.json();
        
        updateDailyChart(trends);
        updateFoodsChart(trends);

        // Fetch recent activity
        const activityResponse = await fetch(`${API_BASE_URL}/logs/confirmations?limit=10`);
        const activity = await activityResponse.json();
        
        updateActivityList(activity);

    } catch (error) {
        console.error('Dashboard error:', error);
        document.getElementById('activity-list').innerHTML = '<p class="no-data">Failed to load dashboard data</p>';
    }
}

// Update daily chart
function updateDailyChart(trends) {
    const ctx = document.getElementById('daily-chart').getContext('2d');
    
    if (dailyChart) {
        dailyChart.destroy();
    }

    const dates = trends.daily_trends?.map(d => new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })) || [];
    const calories = trends.daily_trends?.map(d => d.total_calories) || [];

    dailyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Calories',
                data: calories,
                borderColor: '#FF6B6B',
                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Update foods chart
function updateFoodsChart(trends) {
    const ctx = document.getElementById('foods-chart').getContext('2d');
    
    if (foodsChart) {
        foodsChart.destroy();
    }

    const foods = trends.top_foods?.map(f => f.food_name) || [];
    const counts = trends.top_foods?.map(f => f.count) || [];

    foodsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: foods,
            datasets: [{
                label: 'Count',
                data: counts,
                backgroundColor: [
                    '#FF6B6B',
                    '#4ECDC4',
                    '#45B7D1',
                    '#FFA07A',
                    '#98D8C8'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Update activity list
function updateActivityList(activities) {
    const activityList = document.getElementById('activity-list');
    
    if (!activities || activities.length === 0) {
        activityList.innerHTML = '<p class="no-data">No activity yet</p>';
        return;
    }

    activityList.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-info">
                <div class="activity-food">${activity.selected_food}</div>
                <div class="activity-details">
                    ${Math.round(activity.calories || 0)} cal | 
                    ${activity.protein || 0}g protein | 
                    ${activity.fats || 0}g fat
                </div>
            </div>
            <div class="activity-time">
                ${formatActivityTime(activity.timestamp)}
            </div>
        </div>
    `).join('');
}

// Format activity time
function formatActivityTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Preview image
function showPreview(imageSrc) {
    const modal = document.getElementById('preview-modal');
    const previewImage = document.getElementById('preview-image');
    
    previewImage.src = imageSrc;
    modal.classList.add('active');
}

// Close preview
function closePreview() {
    const modal = document.getElementById('preview-modal');
    modal.classList.remove('active');
}

// Generate session ID
function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Utility: Format number
function formatNumber(num, decimals = 1) {
    return Number(num).toFixed(decimals);
}

// Utility: Capitalize first letter
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Error handling for network issues
window.addEventListener('online', () => {
    console.log('Connection restored');
});

window.addEventListener('offline', () => {
    showError('No internet connection. Please check your network.');
});
