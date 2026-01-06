// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll <= 0) {
        navbar.style.boxShadow = '0 1px 3px rgba(43, 45, 66, 0.08)';
        navbar.style.background = 'rgba(245, 244, 240, 0.95)';
    } else {
        navbar.style.boxShadow = '0 4px 12px rgba(43, 45, 66, 0.15)';
        navbar.style.background = 'rgba(245, 244, 240, 0.98)';
    }

    lastScroll = currentScroll;
});

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all sections
document.querySelectorAll('section').forEach(section => {
    section.style.opacity = '0';
    section.style.transform = 'translateY(20px)';
    section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(section);
});

// CTA button interactions
const ctaButtons = document.querySelectorAll('.primary-button, .pricing-button');

ctaButtons.forEach(button => {
    button.addEventListener('click', function() {
        // Add a ripple effect
        const ripple = document.createElement('span');
        ripple.style.position = 'absolute';
        ripple.style.borderRadius = '50%';
        ripple.style.background = 'rgba(255, 255, 255, 0.5)';
        ripple.style.width = '100px';
        ripple.style.height = '100px';
        ripple.style.marginTop = '-50px';
        ripple.style.marginLeft = '-50px';
        ripple.style.animation = 'ripple 0.6s';
        ripple.style.pointerEvents = 'none';

        this.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    });
});

// Add ripple animation to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        from {
            opacity: 1;
            transform: scale(0);
        }
        to {
            opacity: 0;
            transform: scale(4);
        }
    }

    .primary-button, .pricing-button {
        position: relative;
        overflow: hidden;
    }
`;
document.head.appendChild(style);

// Typing effect for hero subtitle (optional enhancement)
const heroSubtitle = document.querySelector('.hero-subtitle');
const originalText = heroSubtitle.textContent;
let charIndex = 0;

function typeEffect() {
    if (charIndex < originalText.length) {
        heroSubtitle.textContent = originalText.substring(0, charIndex + 1);
        charIndex++;
        setTimeout(typeEffect, 20);
    }
}

// Uncomment to enable typing effect
// heroSubtitle.textContent = '';
// typeEffect();

// Stats counter animation
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// Trigger counter animation when stats come into view
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
            entry.target.classList.add('counted');
            const statValues = entry.target.querySelectorAll('.stat-value');
            // Animation would go here if stats were numbers
        }
    });
});

const heroStats = document.querySelector('.hero-stats');
if (heroStats) {
    statsObserver.observe(heroStats);
}

// Form validation (if forms are added)
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Pricing tier highlighting
const pricingCards = document.querySelectorAll('.pricing-card');
pricingCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.zIndex = '10';
        this.style.transform = 'translateY(-8px) scale(1.02)';
    });

    card.addEventListener('mouseleave', function() {
        this.style.zIndex = '1';
        this.style.transform = 'translateY(0) scale(1)';
    });
});

// Console easter egg
console.log('%cSaddle AdPulse', 'font-size: 20px; font-weight: bold; color: #0891B2;');
console.log('%cLooking for a career opportunity? Email us at careers@saddle.io', 'font-size: 12px; color: #5F6368;');

// Pricing Toggle Functionality
const pricingToggleButtons = document.querySelectorAll('.pricing-toggle-option');
const sellerPricing = document.getElementById('seller-pricing');
const agencyPricing = document.getElementById('agency-pricing');
const pricingSwitchLink = document.querySelector('.pricing-switch-link');

function switchPricingView(targetPlan) {
    // Update toggle buttons
    pricingToggleButtons.forEach(button => {
        const isActive = button.dataset.plan === targetPlan;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-pressed', isActive);
    });

    // Show/hide pricing views
    if (targetPlan === 'seller') {
        sellerPricing.classList.remove('hidden');
        agencyPricing.classList.add('hidden');
    } else {
        sellerPricing.classList.add('hidden');
        agencyPricing.classList.remove('hidden');
    }

    // Smooth scroll to pricing section
    const pricingSection = document.getElementById('pricing');
    if (pricingSection) {
        pricingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Toggle button click handlers
pricingToggleButtons.forEach(button => {
    button.addEventListener('click', function() {
        const targetPlan = this.dataset.plan;
        switchPricingView(targetPlan);
    });

    // Keyboard accessibility
    button.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const targetPlan = this.dataset.plan;
            switchPricingView(targetPlan);
        }
    });
});

// Switch link handler (in seller view footer)
if (pricingSwitchLink) {
    pricingSwitchLink.addEventListener('click', function() {
        const targetPlan = this.dataset.target;
        switchPricingView(targetPlan);
    });

    // Keyboard accessibility
    pricingSwitchLink.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const targetPlan = this.dataset.target;
            switchPricingView(targetPlan);
        }
    });
}

// ICP Card Interactions
const icpCards = document.querySelectorAll('.icp-card');
icpCards.forEach(card => {
    const button = card.querySelector('.icp-cta');
    if (button) {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const icpType = card.dataset.icp;
            
            // Scroll to solution section
            const solutionSection = document.querySelector('.solution-section-v2');
            if (solutionSection) {
                solutionSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }
});

// Agency CTA Button
const agencyCtaButton = document.querySelector('.agency-cta-box .primary-button');
if (agencyCtaButton) {
    agencyCtaButton.addEventListener('click', function() {
        // Switch to agency pricing and scroll
        switchPricingView('agency');
    });
}

// All pricing switch links
const allPricingSwitchLinks = document.querySelectorAll('.pricing-switch-link');
allPricingSwitchLinks.forEach(link => {
    link.addEventListener('click', function() {
        const targetPlan = this.dataset.target;
        switchPricingView(targetPlan);
    });
});

// ========================================
// AUDIT MODAL FUNCTIONALITY
// ========================================

const auditModal = document.getElementById('auditModal');
const closeModalBtn = document.getElementById('closeModal');

// Open modal when any audit trigger is clicked
document.querySelectorAll('.audit-trigger').forEach(trigger => {
    trigger.addEventListener('click', function(e) {
        e.preventDefault();
        openAuditModal();
    });
});

function openAuditModal() {
    auditModal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevent background scroll

    // Initialize quiz if not already done
    if (typeof initializeAuditQuiz === 'function') {
        initializeAuditQuiz();
    }

    // Reset to quiz section
    document.getElementById('quizSection').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('uploadSection').classList.add('hidden');

    // Scroll modal to top
    const modalContainer = auditModal.querySelector('.modal-container');
    if (modalContainer) {
        modalContainer.scrollTop = 0;
    }
}

function closeAuditModal() {
    auditModal.classList.remove('active');
    document.body.style.overflow = ''; // Restore background scroll
}

// Close button click
closeModalBtn.addEventListener('click', closeAuditModal);

// Click outside modal to close
auditModal.addEventListener('click', function(e) {
    if (e.target === auditModal) {
        closeAuditModal();
    }
});

// ESC key to close
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && auditModal.classList.contains('active')) {
        closeAuditModal();
    }
});

// Proceed to upload button (from results section)
const proceedToUploadBtn = document.getElementById('proceedToUploadBtn');
if (proceedToUploadBtn) {
    proceedToUploadBtn.addEventListener('click', function() {
        document.getElementById('resultsSection').classList.add('hidden');
        document.getElementById('uploadSection').classList.remove('hidden');

        // Scroll to top of modal
        const modalContainer = auditModal.querySelector('.modal-container');
        if (modalContainer) {
            modalContainer.scrollTop = 0;
        }
    });
}
