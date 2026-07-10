document.addEventListener("DOMContentLoaded", () => {
  // 1. Ícones Lucide
  if (typeof lucide !== "undefined") lucide.createIcons();

  // 2. Accordion do FAQ
  document.querySelectorAll(".accordion-header").forEach((header) => {
    header.addEventListener("click", function () {
      const item = this.parentElement;
      const content = this.nextElementSibling;
      const isActive = item.classList.contains("active");

      document.querySelectorAll(".accordion-item").forEach((i) => {
        i.classList.remove("active");
        const c = i.querySelector(".accordion-content");
        if (c) c.style.maxHeight = null;
      });

      if (!isActive) {
        item.classList.add("active");
        content.style.maxHeight = content.scrollHeight + "px";
      }
    });
  });

  // 3. Smooth scroll
  document.querySelectorAll(".main-nav a[href^='#']").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute("href"));
      if (target) target.scrollIntoView({ behavior: "smooth" });
    });
  });

  // 4. Auto-fechar mensagens
  document.querySelectorAll(".alert").forEach((msg) => {
    // Auto-fechar após 5 segundos
    setTimeout(() => {
      msg.style.transition = "opacity 0.5s ease";
      msg.style.opacity = "0";
      setTimeout(() => (msg.style.display = "none"), 500);
    }, 5000);

    // Botão de fechar
    const closeBtn = msg.querySelector(".close, .close-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        msg.style.opacity = "0";
        setTimeout(() => (msg.style.display = "none"), 300);
      });
    }

    // Clicar na mensagem fecha
    msg.addEventListener("click", function (e) {
      if (!e.target.closest(".close, .close-btn")) {
        this.style.opacity = "0";
        setTimeout(() => (this.style.display = "none"), 300);
      }
    });
  });
});

// ==========================================================================
// MENU HAMBÚRGUER RESPONSIVO
// ==========================================================================
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const mainNav = document.getElementById('mainNav');
    const body = document.body;

    // Criar overlay
    const overlay = document.createElement('div');
    overlay.className = 'menu-overlay';
    body.appendChild(overlay);

    function toggleMenu() {
        const isOpen = mainNav.classList.toggle('open');
        menuToggle.classList.toggle('active');
        overlay.classList.toggle('active');
        menuToggle.setAttribute('aria-expanded', isOpen);
        body.style.overflow = isOpen ? 'hidden' : '';
    }

    function closeMenu() {
        mainNav.classList.remove('open');
        menuToggle.classList.remove('active');
        overlay.classList.remove('active');
        menuToggle.setAttribute('aria-expanded', 'false');
        body.style.overflow = '';
    }

    // Abrir/fechar ao clicar no botão
    menuToggle.addEventListener('click', toggleMenu);

    // Fechar ao clicar no overlay
    overlay.addEventListener('click', closeMenu);

    // Fechar ao clicar em um link
    const navLinks = mainNav.querySelectorAll('a');
    navLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            // Verifica se é um link âncora (#)
            const href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                closeMenu();
                // Scroll suave para o elemento
                const target = document.querySelector(href);
                if (target) {
                    setTimeout(function() {
                        target.scrollIntoView({ behavior: 'smooth' });
                    }, 300);
                }
            } else {
                closeMenu();
            }
        });
    });

    // Fechar ao pressionar ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && mainNav.classList.contains('open')) {
            closeMenu();
            menuToggle.focus();
        }
    });

    // Fechar ao redimensionar para desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && mainNav.classList.contains('open')) {
            closeMenu();
        }
    });
});