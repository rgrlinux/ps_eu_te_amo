document.addEventListener("DOMContentLoaded", () => {
  // Inicialização dos ícones Lucide
  if (typeof lucide !== "undefined") {
    lucide.createIcons();
  }

  // Lógica do Accordion do FAQ
  const accordionHeaders = document.querySelectorAll(".accordion-header");

  accordionHeaders.forEach((header) => {
    header.addEventListener("click", function () {
      const item = this.parentElement;
      const content = this.nextElementSibling;

      // Verifica se já está ativo
      const isActive = item.classList.contains("active");

      // Fecha todos os itens abertos do Accordion (Comportamento padrão)
      document.querySelectorAll(".accordion-item").forEach((i) => {
        i.classList.remove("active");
        i.querySelector(".accordion-content").style.maxHeight = null;
      });

      // Se não estava ativo antes, abre o atual
      if (!isActive) {
        item.classList.add("active");
        content.style.maxHeight = content.scrollHeight + "px";
      }
    });
  });

  // Smooth scroll básico para links da navbar
  const navLinks = document.querySelectorAll(".main-nav a");
  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      const targetId = link.getAttribute("href");
      if (targetId.startsWith("#")) {
        e.preventDefault();
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          targetElement.scrollIntoView({ behavior: "smooth" });
        }
      }
    });
  });
});
