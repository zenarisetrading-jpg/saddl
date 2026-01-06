// Configuration matching optimizer
const CONFIG = {
    HARVEST_MIN_CLICKS: 10,
    HARVEST_MIN_ORDERS: 3,
    HARVEST_MIN_SALES: 150.00,
    NEGATIVE_CLICKS_THRESHOLD: 10,
    NEGATIVE_SPEND_THRESHOLD: 10.00,
    ROAS_TARGET: 2.50
};

// Quiz questions
const questions = [
    {
        id: 'spend',
        question: "What's your monthly ad spend?",
        options: [
            { value: '500-2000', label: '$500-$2K', midpoint: 1250 },
            { value: '2000-5000', label: '$2K-$5K', midpoint: 3500 },
            { value: '5000-10000', label: '$5K-$10K', midpoint: 7500 },
            { value: '10000-25000', label: '$10K-$25K', midpoint: 17500 },
            { value: '25000+', label: '$25K+', midpoint: 35000 }
        ]
    },
    {
        id: 'acos',
        question: "What's your current ACOS?",
        options: [
            { value: 'under-15', label: 'Under 15%', penalty: 0, acos_midpoint: 12 },
            { value: '15-25', label: '15-25%', penalty: -5, acos_midpoint: 20 },
            { value: '25-35', label: '25-35%', penalty: -15, acos_midpoint: 30 },
            { value: '35-50', label: '35-50%', penalty: -25, acos_midpoint: 42.5 },
            { value: 'over-50', label: 'Over 50%', penalty: -35, acos_midpoint: 60 },
            { value: 'unknown', label: "Don't know", penalty: -20, acos_midpoint: 30 }
        ]
    },
    {
        id: 'campaigns',
        question: "How many active campaigns?",
        options: [
            { value: '1-5', label: '1-5', complexity: 1.0 },
            { value: '5-15', label: '5-15', complexity: 1.2 },
            { value: '15-30', label: '15-30', complexity: 1.5 },
            { value: '30-50', label: '30-50', complexity: 1.8 },
            { value: '50+', label: '50+', complexity: 2.0 }
        ]
    },
    {
        id: 'negatives',
        question: "Last negative keyword addition?",
        options: [
            { value: 'this-week', label: 'This week', penalty: 0, waste_factor: 0.05 },
            { value: 'this-month', label: 'This month', penalty: -8, waste_factor: 0.12 },
            { value: '2-3-months', label: '2-3 months ago', penalty: -18, waste_factor: 0.22 },
            { value: '6-months', label: '6+ months', penalty: -28, waste_factor: 0.35 },
            { value: 'never', label: 'Never', penalty: -35, waste_factor: 0.45 }
        ]
    },
    {
        id: 'harvest',
        question: "Do you run harvest campaigns?",
        options: [
            { value: 'active', label: 'Yes, actively', penalty: 0, opportunity_factor: 0.05 },
            { value: 'started', label: 'Started, not maintaining', penalty: -12, opportunity_factor: 0.15 },
            { value: 'no', label: 'No', penalty: -20, opportunity_factor: 0.25 },
            { value: 'what', label: "What's that?", penalty: -25, opportunity_factor: 0.30 }
        ]
    },
    {
        id: 'competitor',
        question: "Check for competitor ASINs?",
        options: [
            { value: 'weekly', label: 'Weekly', penalty: 0, waste_factor: 0.05 },
            { value: 'monthly', label: 'Monthly', penalty: -8, waste_factor: 0.12 },
            { value: 'rarely', label: 'Rarely', penalty: -15, waste_factor: 0.20 },
            { value: 'never', label: 'Never', penalty: -25, waste_factor: 0.30 }
        ]
    }
];

let quizAnswers = {};
let selectedFile = null;
let quizInitialized = false;

// Initialize quiz
function initQuiz() {
    const container = document.getElementById('questionsContainer');
    questions.forEach((q, idx) => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'question-card';
        questionDiv.innerHTML = `
            <div class="question-header">
                <div class="question-number">${idx + 1}</div>
                <div class="question-content">
                    <h3 class="question-text">${q.question}</h3>
                    <div class="question-checkmark" id="check-${q.id}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </div>
                </div>
            </div>
            <div class="options-modern" id="options-${q.id}">
                ${q.options.map(opt => `
                    <button
                        type="button"
                        class="option-button"
                        data-question="${q.id}"
                        data-value="${opt.value}"
                        onclick='selectAnswer("${q.id}", ${JSON.stringify(opt).replace(/'/g, "&apos;")})'
                    >
                        <span class="option-text">${opt.label}</span>
                        <span class="option-check">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="9 12 11 14 15 10"></polyline>
                            </svg>
                        </span>
                    </button>
                `).join('')}
            </div>
        `;
        container.appendChild(questionDiv);
    });
}

function selectAnswer(questionId, option) {
    // Store answer
    quizAnswers[questionId] = option;

    // Update UI - option buttons
    const options = document.querySelectorAll(`[data-question="${questionId}"]`);
    options.forEach(opt => {
        if (opt.dataset.value === option.value) {
            opt.classList.add('selected');
        } else {
            opt.classList.remove('selected');
        }
    });

    // Show checkmark on question card
    const checkmark = document.getElementById(`check-${questionId}`);
    if (checkmark) {
        checkmark.classList.add('visible');
    }

    // Update progress
    const answeredCount = Object.keys(quizAnswers).length;
    const progress = (answeredCount / questions.length) * 100;

    // Update progress bar
    const progressBar = document.getElementById('progressFill');
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }

    // Update progress counter
    const progressCounter = document.getElementById('progressPercent');
    if (progressCounter) {
        progressCounter.textContent = answeredCount;
    }

    // Enable button when all answered
    const submitBtn = document.getElementById('getScoreBtn');
    if (submitBtn) {
        submitBtn.disabled = answeredCount < questions.length;
        if (answeredCount === questions.length) {
            submitBtn.classList.add('ready');
        } else {
            submitBtn.classList.remove('ready');
        }
    }
}

function calculateQuizScore() {
    let score = 100;
    const spend = quizAnswers.spend?.midpoint || 3500;

    score += quizAnswers.acos?.penalty || 0;
    score += quizAnswers.negatives?.penalty || 0;
    score += quizAnswers.harvest?.penalty || 0;
    score += quizAnswers.competitor?.penalty || 0;

    const competitorWasteFactor = quizAnswers.competitor?.waste_factor || 0.15;
    const competitorWaste = Math.round(spend * competitorWasteFactor * 0.35);

    const negativeWasteFactor = quizAnswers.negatives?.waste_factor || 0.15;
    const zeroConversionWaste = Math.round(spend * negativeWasteFactor * 0.25);

    const harvestFactor = quizAnswers.harvest?.opportunity_factor || 0.15;
    const harvestGain = Math.round(spend * harvestFactor * 0.35);

    const targetAcos = 100 / CONFIG.ROAS_TARGET;
    const currentAcos = quizAnswers.acos?.acos_midpoint || 30;
    const bidWaste = currentAcos > targetAcos ?
        Math.round(spend * (currentAcos - targetAcos) / 100 * 0.5) : 0;

    const negativeGaps = Math.round(spend * negativeWasteFactor * 0.10);

    return {
        score: Math.max(45, Math.min(100, score)),
        total: competitorWaste + zeroConversionWaste + harvestGain + bidWaste + negativeGaps,
        breakdown: [
            { title: 'Competitor ASIN Bleed', amount: competitorWaste, priority: 'high' },
            { title: 'Zero-Conversion Keywords', amount: zeroConversionWaste, priority: 'high' },
            { title: 'Missed Harvests', amount: harvestGain, priority: 'high' },
            { title: 'Bid Inefficiency', amount: bidWaste, priority: 'medium' },
            { title: 'Negative Gaps', amount: negativeGaps, priority: 'medium' }
        ].filter(item => item.amount > 0)
    };
}

function showQuizResults() {
    const results = calculateQuizScore();

    // Hide quiz, show results
    document.getElementById('quizSection').classList.add('hidden');
    document.getElementById('resultsSection').classList.remove('hidden');

    // Update score
    const healthScoreEl = document.getElementById('healthScore');
    healthScoreEl.textContent = results.score;

    // Add color class (using muted brand colors)
    if (results.score >= 80) {
        healthScoreEl.style.color = '#0891B2'; // Brand teal
    } else if (results.score >= 60) {
        healthScoreEl.style.color = '#D4A574'; // Muted amber
    } else {
        healthScoreEl.style.color = '#C27563'; // Muted terracotta
    }

    // Update opportunity
    const low = Math.round(results.total * 0.85);
    const high = Math.round(results.total * 1.15);
    document.getElementById('opportunityAmount').textContent = `$${low.toLocaleString()} - $${high.toLocaleString()}`;

    // Update breakdown
    const breakdownHTML = results.breakdown.map(item => `
        <div class="breakdown-item ${item.priority}">
            <div class="breakdown-header">
                <span class="breakdown-title">${item.title}</span>
                <span class="breakdown-amount">~$${item.amount.toLocaleString()}/mo</span>
            </div>
        </div>
    `).join('');
    document.getElementById('breakdownList').innerHTML = breakdownHTML;

    // Scroll modal to top instead of window
    const modalContainer = document.querySelector('.modal-container');
    if (modalContainer) {
        modalContainer.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function showUploadSection() {
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('uploadSection').classList.remove('hidden');

    // Scroll modal to top instead of window
    const modalContainer = document.querySelector('.modal-container');
    if (modalContainer) {
        modalContainer.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// File upload handlers
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const uploadPrompt = document.getElementById('uploadPrompt');
const fileSelected = document.getElementById('fileSelected');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const analyzeBtn = document.getElementById('analyzeBtn');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');

dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.style.borderColor = '#0891B2';
});

dropzone.addEventListener('dragleave', () => {
    dropzone.style.borderColor = '';
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.style.borderColor = '';
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) handleFileSelect(e.target.files[0]);
});

function handleFileSelect(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = (file.size / 1024).toFixed(1) + ' KB';
    uploadPrompt.classList.add('hidden');
    fileSelected.classList.remove('hidden');
    analyzeBtn.disabled = false;
    errorMessage.classList.add('hidden');
}

analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    errorMessage.classList.add('hidden');

    try {
        // Hide upload section
        document.getElementById('uploadSection').classList.add('hidden');

        // Show processing message
        const processingDiv = document.createElement('section');
        processingDiv.className = 'modal-section';
        processingDiv.id = 'processingSection';
        processingDiv.innerHTML = `
            <div style="text-align: center; padding: 4rem 2rem;">
                <div style="width: 64px; height: 64px; border: 4px solid var(--bg-secondary); border-top: 4px solid var(--accent-primary); border-radius: 50%; margin: 0 auto 2rem; animation: spin 1s linear infinite;"></div>
                <h2 style="font-size: 2rem; margin-bottom: 1rem;">Analyzing Your Data...</h2>
                <p style="color: var(--text-secondary);">Computing waste patterns, harvest opportunities, and optimization potential</p>
            </div>
        `;

        // Insert after upload section
        const uploadSection = document.getElementById('uploadSection');
        uploadSection.parentNode.insertBefore(processingDiv, uploadSection.nextSibling);

        // Add spin animation if not exists
        if (!document.getElementById('spinKeyframes')) {
            const style = document.createElement('style');
            style.id = 'spinKeyframes';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }

        // Parse file (Excel or CSV)
        const results = await analyzeSearchTermReport(selectedFile);

        // Remove processing section
        processingDiv.remove();

        // Show results
        showDetailedResults(results);

    } catch (err) {
        // Remove processing section if exists
        const processingSection = document.getElementById('processingSection');
        if (processingSection) processingSection.remove();

        // Show upload section again
        document.getElementById('uploadSection').classList.remove('hidden');

        errorText.innerHTML = `<strong>Error:</strong> ${err.message}`;
        errorMessage.classList.remove('hidden');

        const modalContainer = document.querySelector('.modal-container');
        if (modalContainer) {
            modalContainer.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
});

// Client-side analysis function (handles Excel and CSV)
async function analyzeSearchTermReport(file) {
    let rows = [];
    let header = [];

    // Check file type
    const isExcel = file.name.match(/\.(xlsx|xls)$/i);
    const isCsv = file.name.match(/\.csv$/i);

    if (!isExcel && !isCsv) {
        throw new Error('Please upload a CSV or Excel file (.csv, .xlsx, .xls)');
    }

    if (isExcel) {
        // Parse Excel file
        const arrayBuffer = await file.arrayBuffer();
        const workbook = XLSX.read(arrayBuffer, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1, defval: '' });

        if (jsonData.length < 2) {
            throw new Error('Excel file appears to be empty or has no data rows');
        }

        header = jsonData[0].map(h => String(h).trim());
        rows = jsonData.slice(1);
    } else {
        // Parse CSV file
        const csvContent = await file.text();
        const lines = csvContent.split('\n');

        if (lines.length < 2) {
            throw new Error('CSV file appears to be empty or invalid');
        }

        header = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        rows = lines.slice(1).map(line => {
            if (!line.trim()) return null;
            return line.split(',').map(v => v.trim().replace(/"/g, ''));
        }).filter(row => row !== null);
    }

    // Find column indices
    const getColumnIndex = (possibleNames) => {
        for (let name of possibleNames) {
            const idx = header.findIndex(h => h.toLowerCase().includes(name.toLowerCase()));
            if (idx !== -1) return idx;
        }
        return -1;
    };

    const indices = {
        searchTerm: getColumnIndex(['Customer Search Term', 'search term', 'keyword']),
        impressions: getColumnIndex(['Impressions']),
        clicks: getColumnIndex(['Clicks']),
        spend: getColumnIndex(['Spend', 'Cost']),
        sales: getColumnIndex(['7 Day Total Sales', 'Total Sales', 'Sales']),
        orders: getColumnIndex(['7 Day Total Orders', 'Total Orders', 'Orders']),
        campaignName: getColumnIndex(['Campaign Name', 'Campaign']),
        startDate: getColumnIndex(['Start Date', 'Date']),
        endDate: getColumnIndex(['End Date'])
    };

    // Validate required columns with better error message
    if (indices.clicks === -1 || indices.spend === -1) {
        const foundColumns = header.slice(0, 10).join(', ');
        throw new Error(`Missing required columns. Found columns: ${foundColumns}... Please make sure your file is an Amazon Search Term Report with Clicks and Spend columns.`);
    }

    // Parse data rows and find date range
    const searchTerms = [];
    let totalSpend = 0;
    let totalSales = 0;
    let totalClicks = 0;
    let minStartDate = null;
    let maxEndDate = null;

    for (const row of rows) {
        if (!row || row.length === 0) continue;

        const getValue = (idx) => idx >= 0 && idx < row.length ? row[idx] : '';

        const clicks = parseFloat(String(getValue(indices.clicks)).replace(/[,$]/g, '')) || 0;
        const spend = parseFloat(String(getValue(indices.spend)).replace(/[,$]/g, '')) || 0;
        const sales = parseFloat(String(getValue(indices.sales)).replace(/[,$]/g, '')) || 0;
        const orders = parseFloat(String(getValue(indices.orders)).replace(/[,$]/g, '')) || 0;

        // Track min start date and max end date
        const startDateStr = String(getValue(indices.startDate));
        const endDateStr = String(getValue(indices.endDate));

        if (startDateStr && startDateStr !== 'undefined' && startDateStr !== '') {
            const startDate = new Date(startDateStr);
            if (!isNaN(startDate)) {
                if (!minStartDate || startDate < minStartDate) {
                    minStartDate = startDate;
                }
            }
        }

        if (endDateStr && endDateStr !== 'undefined' && endDateStr !== '') {
            const endDate = new Date(endDateStr);
            if (!isNaN(endDate)) {
                if (!maxEndDate || endDate > maxEndDate) {
                    maxEndDate = endDate;
                }
            }
        }

        if (clicks > 0 || spend > 0) {
            searchTerms.push({
                searchTerm: String(getValue(indices.searchTerm)),
                impressions: parseFloat(String(getValue(indices.impressions)).replace(/[,$]/g, '')) || 0,
                clicks,
                spend,
                sales,
                orders,
                campaignName: String(getValue(indices.campaignName)),
                roas: sales > 0 ? sales / spend : 0
            });

            totalSpend += spend;
            totalSales += sales;
            totalClicks += clicks;
        }
    }

    if (searchTerms.length === 0) {
        throw new Error('No valid data found in file. Please make sure this is an Amazon Search Term Report with data rows.');
    }

    // Calculate date range and monthly multiplier
    let daysInReport = 30; // Default assumption
    let monthlyMultiplier = 1;

    if (minStartDate && maxEndDate) {
        // Calculate days between min start and max end
        daysInReport = Math.ceil((maxEndDate - minStartDate) / (1000 * 60 * 60 * 24)) + 1;

        if (daysInReport > 0 && daysInReport < 365) {
            monthlyMultiplier = 30 / daysInReport;
        } else if (daysInReport >= 365) {
            // If more than a year, assume it's 30 days (likely data issue)
            daysInReport = 30;
            monthlyMultiplier = 1;
        }
    } else {
        // No date columns found - assume 30 days
        daysInReport = 30;
        monthlyMultiplier = 1;
    }

    // Analysis using CONFIG rules
    const negativeKeywords = searchTerms.filter(st =>
        st.clicks >= CONFIG.NEGATIVE_CLICKS_THRESHOLD &&
        st.spend >= CONFIG.NEGATIVE_SPEND_THRESHOLD &&
        st.orders === 0
    );

    const harvestOpportunities = searchTerms.filter(st =>
        st.clicks >= CONFIG.HARVEST_MIN_CLICKS &&
        st.orders >= CONFIG.HARVEST_MIN_ORDERS &&
        st.sales >= CONFIG.HARVEST_MIN_SALES &&
        st.roas >= CONFIG.ROAS_TARGET
    );

    const lowRoasTerms = searchTerms.filter(st =>
        st.spend > 10 &&
        st.roas > 0 &&
        st.roas < CONFIG.ROAS_TARGET
    );

    // Calculate opportunities (raw from report period)
    const negativeWaste = negativeKeywords.reduce((sum, st) => sum + st.spend, 0);
    const harvestPotential = harvestOpportunities.reduce((sum, st) => sum + (st.sales * 0.15), 0); // 15% lift from exact match
    const bidWaste = lowRoasTerms.reduce((sum, st) => sum + (st.spend * 0.20), 0); // 20% of low ROAS spend

    // Extrapolate to monthly
    const monthlyNegativeWaste = negativeWaste * monthlyMultiplier;
    const monthlyHarvestPotential = harvestPotential * monthlyMultiplier;
    const monthlyBidWaste = bidWaste * monthlyMultiplier;
    const monthlyTotalOpportunity = monthlyNegativeWaste + monthlyHarvestPotential + monthlyBidWaste;
    const monthlySpend = totalSpend * monthlyMultiplier;

    // Calculate health score (inversely correlated with opportunity %)
    // High waste = low score, low waste = high score
    const opportunityPercentage = monthlyTotalOpportunity / Math.max(monthlySpend, 1);

    let healthScore = 100;

    // Penalize based on opportunity percentage
    // 0-5% waste = 90-100 score (excellent)
    // 5-10% waste = 75-90 score (good)
    // 10-20% waste = 60-75 score (needs work)
    // 20%+ waste = 45-60 score (poor)

    if (opportunityPercentage <= 0.05) {
        healthScore = 90 + (1 - opportunityPercentage / 0.05) * 10;
    } else if (opportunityPercentage <= 0.10) {
        healthScore = 75 + (1 - (opportunityPercentage - 0.05) / 0.05) * 15;
    } else if (opportunityPercentage <= 0.20) {
        healthScore = 60 + (1 - (opportunityPercentage - 0.10) / 0.10) * 15;
    } else {
        healthScore = Math.max(45, 60 - Math.min((opportunityPercentage - 0.20) * 100, 15));
    }

    healthScore = Math.round(Math.max(45, Math.min(100, healthScore)));

    // Build issues array (use monthly extrapolated values)
    const issues = [];

    if (negativeKeywords.length > 0) {
        issues.push({
            title: 'Zero-Conversion Keywords',
            description: `Search terms with ${CONFIG.NEGATIVE_CLICKS_THRESHOLD}+ clicks and no sales`,
            amount: Math.round(monthlyNegativeWaste),
            count: negativeKeywords.length,
            priority: 'high',
            type: 'waste'
        });
    }

    if (harvestOpportunities.length > 0) {
        issues.push({
            title: 'Harvest Opportunities',
            description: `High-performing terms ready for exact match campaigns`,
            amount: Math.round(monthlyHarvestPotential),
            count: harvestOpportunities.length,
            priority: 'high',
            type: 'gain'
        });
    }

    if (bidWaste > 0) {
        issues.push({
            title: 'Low ROAS Targets',
            description: `Keywords spending money below target ROAS of ${CONFIG.ROAS_TARGET}x`,
            amount: Math.round(monthlyBidWaste),
            count: lowRoasTerms.length,
            priority: 'medium',
            type: 'waste'
        });
    }

    return {
        healthScore,
        totalOpportunity: Math.round(monthlyTotalOpportunity),
        totals: {
            spend: Math.round(monthlySpend),
            sales: Math.round(totalSales * monthlyMultiplier),
            roas: totalSpend > 0 ? (totalSales / totalSpend) : 0
        },
        dataQuality: {
            validRows: searchTerms.length,
            daysInReport,
            monthlyMultiplier: monthlyMultiplier.toFixed(2)
        },
        issues
    };
}

// Function to show detailed results from analysis
function showDetailedResults(data) {
    // Hide all other sections
    document.getElementById('quizSection').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('uploadSection').classList.add('hidden');

    // Create or get detailed results section within modal
    let detailedSection = document.getElementById('detailedResultsSection');
    if (!detailedSection) {
        detailedSection = document.createElement('section');
        detailedSection.id = 'detailedResultsSection';
        detailedSection.className = 'modal-section';
        document.querySelector('.modal-container').appendChild(detailedSection);
    }

    // Create detailed results content
    const resultsHTML = `
        <div class="results-grid-modal">
            <div class="container">
                <div class="results-grid">
                    <!-- Health Score -->
                    <div class="result-card score-card">
                        <h2>Your Actual PPC Health Score</h2>
                        <div class="health-score" style="color: ${getScoreColor(data.healthScore)};">
                            ${data.healthScore}
                        </div>
                        <p class="score-subtitle">Based on ${data.dataQuality.validRows.toLocaleString()} search terms (${data.dataQuality.daysInReport} days extrapolated to 30 days)</p>
                    </div>

                    <!-- Total Opportunity -->
                    <div class="result-card opportunity-card">
                        <div class="card-header">
                            <h3>Total Monthly Opportunity</h3>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="opportunity-icon">
                                <line x1="12" y1="1" x2="12" y2="23"></line>
                                <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                            </svg>
                        </div>
                        <div class="opportunity-amount">$${data.totalOpportunity.toLocaleString()}</div>
                        <p class="opportunity-subtitle">in recoverable waste + missed gains</p>
                    </div>

                    <!-- Account Overview -->
                    <div class="result-card">
                        <h3 style="margin-bottom: 1.5rem;">Account Overview</h3>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem;">
                            <div>
                                <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">Total Spend</div>
                                <div style="font-size: 1.8rem; font-weight: 700;">$${data.totals.spend.toLocaleString()}</div>
                            </div>
                            <div>
                                <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">Total Sales</div>
                                <div style="font-size: 1.8rem; font-weight: 700;">$${data.totals.sales.toLocaleString()}</div>
                            </div>
                            <div>
                                <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">ROAS</div>
                                <div style="font-size: 1.8rem; font-weight: 700;">${data.totals.roas.toFixed(2)}x</div>
                            </div>
                        </div>
                    </div>

                    <!-- Issues Breakdown -->
                    <div class="result-card">
                        <h3 style="margin-bottom: 1.5rem;">Where Your Money Is Going</h3>
                        <div class="breakdown-list">
                            ${data.issues.map(issue => `
                                <div class="breakdown-item ${issue.priority}">
                                    <div class="breakdown-header">
                                        <div>
                                            <span style="padding: 0.3rem 0.8rem; background: ${issue.priority === 'high' ? 'rgba(194, 117, 99, 0.1)' : 'rgba(212, 165, 116, 0.1)'}; color: ${issue.priority === 'high' ? '#C27563' : '#D4A574'}; border-radius: 100px; font-size: 0.75rem; font-weight: 700; margin-right: 0.8rem;">${issue.priority.toUpperCase()}</span>
                                            <span class="breakdown-title">${issue.title}</span>
                                            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 0.5rem;">${issue.description}</p>
                                            ${issue.count ? `<p style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">${issue.count} items found</p>` : ''}
                                        </div>
                                        <div class="breakdown-amount" style="color: ${issue.type === 'gain' ? '#0891B2' : '#C27563'};">
                                            ${issue.type === 'gain' ? '+' : '-'}$${Math.round(issue.amount).toLocaleString()}/mo
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- CTA to Full Product -->
                    <div class="upload-cta-card result-card">
                        <div class="upload-cta-content">
                            <div class="upload-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <path d="M12 16v-4"></path>
                                    <path d="M12 8h.01"></path>
                                </svg>
                            </div>
                            <div class="upload-cta-text">
                                <h3>Ready to Fix These Issues?</h3>
                                <p>Saddle AdPulse can automatically:</p>
                                <ul class="upload-benefits">
                                    <li>Generate bulk files to add ${data.issues.find(i => i.title.includes('Zero-Conversion'))?.count || 0} negative keywords</li>
                                    <li>Create ${data.issues.find(i => i.title.includes('Harvest'))?.count || 0} exact match harvest campaigns</li>
                                    <li>Optimize bids across all campaigns for target ROAS</li>
                                    <li>Simulate changes before applying</li>
                                    <li>AI analyst to answer performance questions</li>
                                </ul>
                            </div>
                        </div>
                        <button id="goToPricingBtn" class="primary-button large" style="width: 100%;">
                            Start Free Trial - Fix These Issues →
                        </button>
                        <p class="upload-disclaimer">14-day free trial • No credit card required • Cancel anytime</p>
                    </div>

                    <!-- Restart -->
                    <div style="text-align: center; margin-top: 2rem;">
                        <button id="restartAuditBtn" class="secondary-button" style="background: none; border: 2px solid var(--bg-secondary); color: var(--text-secondary); cursor: pointer; padding: 0.75rem 1.5rem; border-radius: 8px; font-size: 0.95rem;">
                            ← Analyze Another Account
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Insert results into modal section
    detailedSection.innerHTML = resultsHTML;
    detailedSection.classList.remove('hidden');

    // Add pricing button handler
    document.getElementById('goToPricingBtn').addEventListener('click', function() {
        // Close modal
        const modal = document.getElementById('auditModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }

        // Scroll to pricing section
        setTimeout(() => {
            const pricingSection = document.getElementById('pricing');
            if (pricingSection) {
                pricingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 300);
    });

    // Add restart button handler
    document.getElementById('restartAuditBtn').addEventListener('click', function() {
        // Reset to quiz section
        detailedSection.classList.add('hidden');
        document.getElementById('quizSection').classList.remove('hidden');
        document.getElementById('resultsSection').classList.add('hidden');
        document.getElementById('uploadSection').classList.add('hidden');

        // Reset quiz state
        quizAnswers = {};
        selectedFile = null;

        // Reset progress
        const progressBar = document.getElementById('progressFill');
        if (progressBar) progressBar.style.width = '0%';

        const progressCounter = document.getElementById('progressPercent');
        if (progressCounter) progressCounter.textContent = '0';

        // Reset button
        const submitBtn = document.getElementById('getScoreBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.remove('ready');
        }

        // Clear all selections
        document.querySelectorAll('.option-button.selected').forEach(btn => {
            btn.classList.remove('selected');
        });
        document.querySelectorAll('.question-checkmark.visible').forEach(check => {
            check.classList.remove('visible');
        });

        // Scroll to top
        const modalContainer = document.querySelector('.modal-container');
        if (modalContainer) modalContainer.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Scroll modal to top
    const modalContainer = document.querySelector('.modal-container');
    if (modalContainer) {
        modalContainer.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function getScoreColor(score) {
    if (score >= 80) return '#0891B2'; // Brand teal
    if (score >= 60) return '#D4A574'; // Muted amber
    return '#C27563'; // Muted terracotta
}

// Initialize quiz when called (will be triggered by modal open)
function initializeAuditQuiz() {
    if (!quizInitialized) {
        const getScoreBtn = document.getElementById('getScoreBtn');
        if (getScoreBtn) {
            getScoreBtn.addEventListener('click', showQuizResults);
        }
        initQuiz();
        quizInitialized = true;
    }
}

// Auto-initialize if elements exist (for standalone audit.html page)
if (document.getElementById('questionsContainer')) {
    initializeAuditQuiz();
}
