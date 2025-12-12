document.addEventListener('DOMContentLoaded', () => {

    // Translations
    const translations = {
        fr: {
            nav_vision: "Vision",
            nav_platform: "Plateforme",
            nav_solutions: "Solutions",
            nav_technology: "Technologie",
            nav_beta: "Bêta",
            hero_title: "Gradient Systems",
            hero_strong: "Une technologie de pointe, pensée pour les Pros, adaptée pour les Particuliers.",
            hero_subtitle: "La technologie réduit l'écart. La communauté fait la différence.",
            hero_cta_offer: "Découvrir les Offres",
            hero_cta_more: "Notre Vision",
            tech_title: "Technologie Propriétaire",
            tech_subtitle: "Une infrastructure de pointe conçue pour la performance et la rigueur scientifique.",
            card_backtest_title: "Création & Backtest",
            card_backtest_desc: "Développez et backtestez vos stratégies en Python avec notre moteur ultra-rapide. Accédez à des métriques institutionnelles (Ratio de Sharpe, Sortino, Max Drawdown).",
            card_risk_title: "Gestion du Risque Avancée",
            card_risk_desc: "Utilisez nos simulations Monte Carlo et nos outils d'analyse de covariance pour stress-tester vos modèles.",
            card_intel_title: "Intelligence Collective",
            card_intel_desc: "Participez aux analyses et utilisez les indicateurs de marché et prévisions issus de la communauté pour affiner vos décisions.",
            preview_title: "Aperçu de la Plateforme",
            preview_subtitle: "Une ergonomie intuitive pour des décisions stratégiques.",
            preview_caption_chart: "Analyse Technique & Indicateurs",
            preview_caption_metrics: "Métriques Institutionnelles",
            preview_caption_drawdown: "Contrôle du Risque & Monte Carlo",
            offer_title: "Nos Solutions",
            offer_subtitle: "Que vous soyez débutant ou professionnel, nous avons l'outil qu'il vous faut.",
            retail_badge: "Investisseurs Particuliers",
            retail_title: "Changez de Dimension",
            retail_desc: "Un outil professionnel accessible à tous. Ne tradez plus seul : profitez de l'intelligence collective pour sécuriser votre capital.",
            retail_feat_1: "Analyses de niveau Institutionnel",
            retail_feat_2: "Leaderboard & Validation par les pairs",
            retail_feat_3: "Montée en compétence continue",
            retail_feat_4: "Tarification adaptée à votre évolution",
            pro_badge: "Professionnels & Fonds",
            pro_title: "Optimisez votre Gestion",
            pro_desc: "Asset Managers & Family Offices : complétez votre arsenal. Déléguez la complexité quantitative pour vous concentrer sur vos clients.",
            pro_feat_1: "Création de stratégie ultra-rapide",
            pro_feat_2: "Reporting Client (Conformité MiFID)",
            pro_feat_3: "Exports marque blanche",
            pro_feat_4: "Validation de risque avancée",
            contact_title: "Rejoindre la Bêta Privée",
            contact_subtitle: "Notre MVP est opérationnel. Participez à la révolution du trading quantitatif dès maintenant.",
            form_name_label: "Nom Complet / Société",
            form_email_label: "Adresse Email Professionnelle",
            form_type_label: "Votre Profil",
            form_type_retail: "Investisseur Particulier",
            form_type_pro: "Professionnel / Institutionnel",
            form_submit: "Demander mon accès Bêta",
            form_name_placeholder: "Votre Nom",
            form_email_placeholder: "nom@exemple.com",
            form_message_placeholder: "Dites-nous en plus sur vos besoins..."
        },
        en: {
            nav_vision: "Vision",
            nav_platform: "Platform",
            nav_solutions: "Solutions",
            nav_technology: "Technology",
            nav_beta: "Beta",
            hero_title: "Gradient Systems",
            hero_strong: "Advanced technology, designed for Pros, adapted for Retail.",
            hero_subtitle: "Technology bridges the gap. Community makes the difference.",
            hero_cta_offer: "Discover Offers",
            hero_cta_more: "Our Vision",
            tech_title: "Proprietary Technology",
            tech_subtitle: "State-of-the-art infrastructure designed for performance and scientific rigor.",
            card_backtest_title: "Creation & Backtest",
            card_backtest_desc: "Develop and backtest your strategies in Python with our ultra-fast engine. Access institutional metrics (Sharpe Ratio, Sortino, Max Drawdown).",
            card_risk_title: "Advanced Risk Management",
            card_risk_desc: "Use our Monte Carlo simulations and covariance analysis tools to stress-test your models.",
            card_intel_title: "Collective Intelligence",
            card_intel_desc: "Participate in analysis and use market indicators and forecasts from the community to refine your decisions.",
            preview_title: "Platform Preview",
            preview_subtitle: "Clear interface for informed decisions.",
            preview_caption_chart: "Technical Analysis & Indicators",
            preview_caption_metrics: "Institutional Metrics",
            preview_caption_drawdown: "Risk Control & Monte Carlo",
            offer_title: "Our Solutions",
            offer_subtitle: "Whether you are a beginner or an asset manager, we have the right tool for you.",
            retail_badge: "Retail Investors",
            retail_title: "Level Up Your Trading",
            retail_desc: "Professional tools finally accessible to all. Don't trade alone: leverage collective intelligence to secure your capital.",
            retail_feat_1: "Institutional Level Analysis",
            retail_feat_2: "Leaderboard & Peer Validation",
            retail_feat_3: "Continuous Skill Improvement",
            retail_feat_4: "Pricing Adapted to Your Growth",
            pro_badge: "Professionals & Funds",
            pro_title: "Optimize Your Management",
            pro_desc: "Asset Managers & Family Offices: complete your arsenal. Delegate quantitative complexity to focus on your clients.",
            pro_feat_1: "Ultra-fast Strategy Creation",
            pro_feat_2: "Client Reporting (MiFID Compliance)",
            pro_feat_3: "White Label Exports",
            pro_feat_4: "Advanced Risk Validation",
            contact_title: "Join the Private Beta",
            contact_subtitle: "Our MVP is live. Join the quantitative trading revolution now.",
            form_name_label: "Full Name / Company",
            form_email_label: "Professional Email Address",
            form_type_label: "Your Profile",
            form_type_retail: "Retail Investor",
            form_type_pro: "Professional / Institutional",
            form_submit: "Request Beta Access",
            form_name_placeholder: "Your Name",
            form_email_placeholder: "name@example.com",
            form_message_placeholder: "Tell us more about your needs..."
        }
    };

    // Language Handling
    const langToggle = document.getElementById('lang-toggle');
    let currentLang = localStorage.getItem('lang') || 'fr';

    function setLanguage(lang) {
        currentLang = lang;
        localStorage.setItem('lang', lang);

        // Update Text
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            if (translations[lang][key]) {
                element.innerHTML = translations[lang][key];
            }
        });

        // Update Placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            if (translations[lang][key]) {
                element.placeholder = translations[lang][key];
            }
        });

        if (langToggle) {
            langToggle.innerText = lang === 'fr' ? 'EN' : 'FR';
        }

        // Update Mobile Button Text
        const mobileLangToggle = document.getElementById('mobile-lang-toggle');
        if (mobileLangToggle) {
            mobileLangToggle.innerText = lang === 'fr' ? 'EN' : 'FR';
        }
    }

    // Initialize Language
    setLanguage(currentLang);

    // Toggle Button Listener
    if (langToggle) {
        langToggle.addEventListener('click', () => {
            setLanguage(currentLang === 'fr' ? 'en' : 'fr');
        });
    }

    const mobileLangToggle = document.getElementById('mobile-lang-toggle');
    if (mobileLangToggle) {
        mobileLangToggle.addEventListener('click', () => {
            setLanguage(currentLang === 'fr' ? 'en' : 'fr');
        });
    }

    // --- Mobile Menu Logic ---
    const mobileToggle = document.querySelector('.mobile-toggle');
    const mobileOverlay = document.querySelector('.mobile-menu-overlay');
    const mobileLinks = document.querySelectorAll('.mobile-nav-content a');

    if (mobileToggle && mobileOverlay) {
        // Toggle Menu
        mobileToggle.addEventListener('click', () => {
            mobileToggle.classList.toggle('open');
            mobileOverlay.classList.toggle('open');
            document.body.style.overflow = mobileOverlay.classList.contains('open') ? 'hidden' : ''; // Prevent scroll
        });

        // Close on Link Click
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileToggle.classList.remove('open');
                mobileOverlay.classList.remove('open');
                document.body.style.overflow = '';
            });
        });
    }

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                // Fixed offset: Align top of section to top of viewport (minus header/padding)
                // This ensures titles always start at the same vertical position.
                const offset = 80; // Space for header
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - offset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Parallax Effect for Background Blobs
    document.addEventListener('mousemove', (e) => {
        const x = e.clientX / window.innerWidth;
        const y = e.clientY / window.innerHeight;

        const blob1 = document.querySelector('.blob-1');
        const blob2 = document.querySelector('.blob-2');

        if (blob1) {
            blob1.style.transform = `translate(${x * -50}px, ${y * -50}px)`;
        }
        if (blob2) {
            blob2.style.transform = `translate(${x * 50}px, ${y * 50}px)`;
        }
    });

    // Contact Form Handling (Formspree AJAX)
    const contactForm = document.getElementById('contactForm');

    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();

            // ⚠️ IMPORTANT: Inscrire votre ID Formspree ici
            // Créez un compte sur https://formspree.io/ (gratuit)
            // Créez un formulaire et copiez l'ID (ex: "xvgzlqwp")
            const FORMSPREE_ID = "xjknpoeb";

            const btn = contactForm.querySelector('button');
            const originalText = btn.innerText;
            const loadingText = currentLang === 'fr' ? "Envoi en cours..." : "Sending...";
            const successText = currentLang === 'fr' ? "Message envoyé !" : "Message sent!";
            const errorText = currentLang === 'fr' ? "Erreur. Réessayez." : "Error. Try again.";

            // Visual Feedback
            btn.innerText = loadingText;
            btn.disabled = true;
            btn.style.background = "linear-gradient(135deg, #00f2ff, #0066ff)"; // Reverse gradient

            const data = new FormData(contactForm);

            // Fetch to Formspree
            fetch(`https://formspree.io/f/${FORMSPREE_ID}`, {
                method: "POST",
                body: data,
                headers: {
                    'Accept': 'application/json'
                }
            }).then(response => {
                if (response.ok) {
                    btn.innerText = successText;
                    btn.style.background = "#28a745"; // Green
                    contactForm.reset();
                    setTimeout(() => {
                        btn.innerText = originalText;
                        btn.style.background = "";
                        btn.disabled = false;
                    }, 4000);
                } else {
                    response.json().then(data => {
                        if (Object.hasOwn(data, 'errors')) {
                            // Optional: detailed error handling
                            console.error(data["errors"]);
                        }
                    });
                    btn.innerText = errorText;
                    setTimeout(() => {
                        btn.innerText = originalText;
                        btn.style.background = "";
                        btn.disabled = false;
                    }, 3000);
                }
            }).catch(error => {
                btn.innerText = errorText;
                setTimeout(() => {
                    btn.innerText = originalText;
                    btn.style.background = "";
                    btn.disabled = false;
                }, 3000);
            });
        });
    }

    // --- MODAL / LIGHTBOX LOGIC ---
    const modal = document.getElementById("preview-modal");
    const modalImgContainer = document.getElementById("modal-img-container");
    const span = document.getElementsByClassName("close-modal")[0];

    // Get all preview items
    const previewItems = document.querySelectorAll(".preview-item");

    previewItems.forEach(item => {
        item.addEventListener('click', function () {
            modal.style.display = "flex";
            modal.style.justifyContent = "center";
            modal.style.alignItems = "center";

            // Clear previous content
            modalImgContainer.innerHTML = '';

            // Get images from the clicked item
            const images = this.querySelectorAll(".preview-img");

            // Clone and append each image
            images.forEach(img => {
                const clonedImg = img.cloneNode();
                clonedImg.style.maxHeight = "85vh"; // Prevent being too tall
                clonedImg.style.width = "auto";
                clonedImg.style.maxWidth = "100%";
                clonedImg.style.objectFit = "contain";
                clonedImg.style.marginBottom = "20px";
                modalImgContainer.appendChild(clonedImg);
            });
        });
    });

    // Close the modal
    if (span) {
        span.onclick = function () {
            modal.style.display = "none";
        }
    }

    // Close on click outside
    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    // Scroll Animation Observer (Reveal elements on scroll)
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Initial styles for scroll animation
    const animateElements = document.querySelectorAll('.card, .section-title, .hero h1, .hero p, .contact-container');

    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
        observer.observe(el);
    });
});
