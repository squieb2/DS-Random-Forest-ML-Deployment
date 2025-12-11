
const form = document.getElementById('predictionForm');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const result = document.getElementById('result');
const predictBtn = document.getElementById('predictBtn');

// Cache for sample data
let sampleData = null;
let currentPresetId = null;

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    result.classList.remove('show');
    error.classList.remove('show');

    loading.classList.add('show')
    predictBtn.disabled = true;

    const formData = new FormData(e.target);
    const data = {};

    for (let [key, value] of formData.entries()) {
        data[key] = parseFloat(value);
    }

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const resultData = await response.json();

        loading.classList.remove('show');
        predictBtn.disabled = false;

        if (resultData.status === 'success') {
            displayResults(resultData);
        } else {
            showError(resultData.message || 'Unknown error occurred')
        }
    } catch (err) {
        loading.classList.remove('show');
        predictBtn.disabled = false;
        showError('Connection error: ' + err.message)
    }

});

function displayResults(data) {
    document.getElementById('predictionValue').textContent = data.prediction;

    document.getElementById('confidenceValue').textContent =
        `Confidence: ${(data.confidence * 100).toFixed(1)}%`;

    const probsContainer = document.getElementById('probabilitiesContainer');
    probsContainer.innerHTML = '';

    const sortedProbs = Object.entries(data.probabilities).sort((a, b) => b[1] - a[1]);

    sortedProbs.forEach(([className, prob]) => {
        const percentage = (prob * 100).toFixed(1);

        const probItem = document.createElement('div');
        probItem.className = 'prob-item';
        probItem.innerHTML = `
            <span class="prob-label">${className}</span>
            <div class="prob-bar-container">
                <div class="prob-bar" style="width: ${percentage}%">
                    <span class="prob-value">${percentage}%</span>
                </div>
            </div>
            <span class="prob-percentage">${percentage}%</span>
        `;

        probsContainer.appendChild(probItem);
    });

    // Show expected vs actual if preset was used
    const predictionCard = document.querySelector('.prediction-card');
    const existingComparison = predictionCard.querySelector('.prediction-comparison');
    if (existingComparison) {
        existingComparison.remove();
    }

    if (currentPresetId && sampleData) {
        const preset = sampleData.presets.find(p => p.id === currentPresetId);
        if (preset) {
            const isCorrect = preset.expectedClass === data.prediction;
            const comparisonDiv = document.createElement('div');
            comparisonDiv.className = `prediction-comparison ${isCorrect ? 'correct' : 'different'}`;
            comparisonDiv.innerHTML = `
                <strong>Expected:</strong> ${preset.expectedClass} |
                <strong>Actual:</strong> ${data.prediction}
                ${isCorrect ? ' ✓' : ' (Different result)'}
            `;
            predictionCard.appendChild(comparisonDiv);
        }
    }

    result.classList.add('show');

    result.scrollIntoView({ behavior: 'auto', block: 'nearest'});
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    error.classList.add('show');
}

form.addEventListener('reset', () => {
    result.classList.remove('show');
    error.classList.remove('show');
    document.getElementById('sampleIndicator').classList.remove('show');
    currentPresetId = null;
});

// Load sample data on page load
async function loadSampleData() {
    try {
        const response = await fetch('/api/samples');
        const data = await response.json();
        if (data.status === 'success') {
            sampleData = data;
            console.log('Sample data loaded:', data.totalSamples, 'presets');
        }
    } catch (err) {
        console.error('Failed to load sample data:', err);
    }
}

// Generate random sample within valid ranges
function generateRandomSample() {
    if (!sampleData) {
        showError('Sample data not loaded yet. Please try again.');
        return;
    }

    const ranges = sampleData.featureRanges;

    Object.keys(ranges).forEach(feature => {
        const input = document.getElementById(feature);
        if (input) {
            const range = ranges[feature];
            // Generate value within 1 std dev of mean for realistic samples
            const min = Math.max(range.min, range.mean - range.std);
            const max = Math.min(range.max, range.mean + range.std);
            const randomValue = min + Math.random() * (max - min);
            input.value = randomValue.toFixed(2);
        }
    });

    currentPresetId = null;
    showSampleIndicator('Random sample generated');
    hideRangesPanel();
}

// Load preset sample
function loadPreset(presetId) {
    if (!sampleData) {
        showError('Sample data not loaded yet. Please try again.');
        return;
    }

    const preset = sampleData.presets.find(p => p.id === presetId);
    if (!preset) {
        showError('Preset not found.');
        return;
    }

    Object.keys(preset.features).forEach(feature => {
        const input = document.getElementById(feature);
        if (input) {
            input.value = preset.features[feature];
        }
    });

    currentPresetId = presetId;
    showSampleIndicator(
        `${preset.name} loaded (Expected: ${preset.expectedClass})`
    );
    closePresetModal();
}

// Show preset selection modal
function showPresetModal() {
    if (!sampleData) {
        showError('Sample data not loaded yet. Please try again.');
        return;
    }

    const modal = document.getElementById('presetModal');
    const presetList = document.getElementById('presetList');

    // Build preset cards
    presetList.innerHTML = sampleData.presets.map(preset => `
        <div class="preset-card" onclick="loadPreset(${preset.id})">
            <h4>${preset.name}</h4>
            <p class="preset-description">${preset.description}</p>
            <p class="preset-expected">Expected: <strong>${preset.expectedClass}</strong></p>
        </div>
    `).join('');

    modal.classList.add('show');
}

function closePresetModal() {
    document.getElementById('presetModal').classList.remove('show');
}

// Show feature ranges panel
function showRangesPanel() {
    if (!sampleData) {
        showError('Sample data not loaded yet. Please try again.');
        return;
    }

    const panel = document.getElementById('rangesPanel');
    const content = document.getElementById('rangesContent');

    const ranges = sampleData.featureRanges;
    content.innerHTML = Object.keys(ranges).map(feature => {
        const r = ranges[feature];
        return `
            <div class="range-item">
                <div class="range-label">${feature.replace(/_/g, ' ')}</div>
                <div class="range-values">
                    <span>Min: ${r.min.toFixed(2)}</span>
                    <span>Mean: ${r.mean.toFixed(2)}</span>
                    <span>Max: ${r.max.toFixed(2)}</span>
                </div>
            </div>
        `;
    }).join('');

    panel.classList.add('show');
}

function hideRangesPanel() {
    document.getElementById('rangesPanel').classList.remove('show');
}

function showSampleIndicator(message) {
    const indicator = document.getElementById('sampleIndicator');
    const text = indicator.querySelector('.indicator-text');
    text.textContent = message;
    indicator.classList.add('show');
}

// Initialize sample data on page load
loadSampleData();

// Quick action button listeners
document.getElementById('randomSampleBtn').addEventListener('click', generateRandomSample);
document.getElementById('loadPresetBtn').addEventListener('click', showPresetModal);
document.getElementById('showRangesBtn').addEventListener('click', showRangesPanel);
document.getElementById('closeModal').addEventListener('click', closePresetModal);
document.getElementById('closeRanges').addEventListener('click', hideRangesPanel);

// Hide indicator when user manually edits
document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('input', () => {
        document.getElementById('sampleIndicator').classList.remove('show');
        currentPresetId = null;
    });
});

// Close modal on outside click
document.getElementById('presetModal').addEventListener('click', (e) => {
    if (e.target.id === 'presetModal') {
        closePresetModal();
    }
});