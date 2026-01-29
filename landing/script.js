// Smooth scroll for navigation links
// IMPORTANT: Exclude modal triggers (.audit-trigger, .beta-signup-trigger) - they have their own handlers
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        // Skip if this is a modal trigger - let its dedicated handler run
        if (this.classList.contains('audit-trigger') || this.classList.contains('beta-signup-trigger')) {
            return; // Don't prevent default, don't scroll - let modal handler take over
        }

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


// Navbar scroll effect (throttled to ~60fps)
const navbar = document.querySelector('.navbar');
let scrollTicking = false;

window.addEventListener('scroll', () => {
    if (!scrollTicking) {
        requestAnimationFrame(() => {
            const currentScroll = window.pageYOffset;
            if (currentScroll <= 0) {
                navbar.style.boxShadow = '0 1px 3px rgba(43, 45, 66, 0.08)';
                navbar.style.background = 'rgba(245, 244, 240, 0.95)';
            } else {
                navbar.style.boxShadow = '0 4px 12px rgba(43, 45, 66, 0.15)';
                navbar.style.background = 'rgba(245, 244, 240, 0.98)';
            }
            scrollTicking = false;
        });
        scrollTicking = true;
    }
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

// Observe all sections EXCEPT those inside modals
// Modal sections have their own visibility controlled by JS
document.querySelectorAll('section').forEach(section => {
    // Skip sections inside modal overlays - they shouldn't be affected by scroll animations
    if (section.closest('.modal-overlay')) {
        return;
    }
    section.style.opacity = '0';
    section.style.transform = 'translateY(20px)';
    section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(section);

});

// CTA button interactions
const ctaButtons = document.querySelectorAll('.primary-button, .pricing-button');

ctaButtons.forEach(button => {
    button.addEventListener('click', function () {
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
// NOTE: Wrapped in null check - not all pages have .hero-subtitle
const heroSubtitle = document.querySelector('.hero-subtitle');
if (heroSubtitle) {
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
}

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

// Form validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Pricing tier highlighting
const pricingCards = document.querySelectorAll('.pricing-card');
pricingCards.forEach(card => {
    card.addEventListener('mouseenter', function () {
        this.style.zIndex = '10';
        this.style.transform = 'translateY(-8px) scale(1.02)';
    });

    card.addEventListener('mouseleave', function () {
        this.style.zIndex = '1';
        this.style.transform = 'translateY(0) scale(1)';
    });
});

// Console easter egg
console.log('%cSaddle AdPulse', 'font-size: 20px; font-weight: bold; color: #0891B2;');
console.log('%cLooking for a career opportunity? Email us at careers@saddle.io', 'font-size: 12px; color: #5F6368;');

// ========================================
// AUDIT MODAL FUNCTIONALITY
// ========================================

const auditModal = document.getElementById('auditModal');
const closeModalBtn = document.getElementById('closeModal');

// Open modal when any audit trigger is clicked
document.querySelectorAll('.audit-trigger').forEach(trigger => {
    trigger.addEventListener('click', function (e) {
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
auditModal.addEventListener('click', function (e) {
    if (e.target === auditModal) {
        closeAuditModal();
    }
});

// ESC key to close any active modal
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        if (auditModal.classList.contains('active')) closeAuditModal();
        if (betaModal && betaModal.classList.contains('active')) closeBetaModal();
    }
});

// Proceed to upload button (from results section)
const proceedToUploadBtn = document.getElementById('proceedToUploadBtn');
if (proceedToUploadBtn) {
    proceedToUploadBtn.addEventListener('click', function () {
        document.getElementById('resultsSection').classList.add('hidden');
        document.getElementById('uploadSection').classList.remove('hidden');

        // Scroll to top of modal
        const modalContainer = auditModal.querySelector('.modal-container');
        if (modalContainer) {
            modalContainer.scrollTop = 0;
        }
    });
}

// ========================================
// BETA SIGNUP MODAL FUNCTIONALITY
// ========================================

const betaModal = document.getElementById('betaSignupModal');
const closeBetaModalBtn = document.getElementById('closeBetaModal');
const betaSignupForm = document.getElementById('betaSignupForm');
const betaSuccessMessage = document.getElementById('betaSuccessMessage');
const closeBetaSuccess = document.getElementById('closeBetaSuccess');

// Open beta modal when any beta-signup-trigger is clicked
document.querySelectorAll('.beta-signup-trigger').forEach(trigger => {
    trigger.addEventListener('click', function (e) {
        e.preventDefault();
        openBetaModal();
    });
});

function openBetaModal() {
    betaModal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Reset form and show it
    betaSignupForm.reset();
    betaSignupForm.style.display = 'block';
    betaSuccessMessage.classList.add('hidden');

    // Scroll modal to top
    const modalContainer = betaModal.querySelector('.modal-container');
    if (modalContainer) {
        modalContainer.scrollTop = 0;
    }
}

function closeBetaModal() {
    betaModal.classList.remove('active');
    document.body.style.overflow = '';
}

// Close button click
closeBetaModalBtn.addEventListener('click', closeBetaModal);

// Close success message button
closeBetaSuccess.addEventListener('click', closeBetaModal);

// Click outside modal to close
betaModal.addEventListener('click', function (e) {
    if (e.target === betaModal) {
        closeBetaModal();
    }
});

// Handle beta signup form submission
betaSignupForm.addEventListener('submit', function (e) {
    e.preventDefault();

    // Collect form data
    const formData = {
        name: document.getElementById('betaName').value,
        email: document.getElementById('betaEmail').value,
        role: document.getElementById('betaRole').value,
        accounts: document.getElementById('betaAccounts').value,
        spend: document.getElementById('betaSpend').value,
        goal: document.getElementById('betaGoal').value,
        timestamp: new Date().toISOString()
    };

    // Log to console (in production, send to backend/API)
    console.log('Beta Signup Data:', formData);

    // TODO: Send to backend API
    // fetch('/api/beta-signup', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify(formData)
    // });

    // Show success message
    betaSignupForm.style.display = 'none';
    betaSuccessMessage.classList.remove('hidden');

    // Scroll to top of modal
    const modalContainer = betaModal.querySelector('.modal-container');
    if (modalContainer) {
        modalContainer.scrollTop = 0;
    }
});

