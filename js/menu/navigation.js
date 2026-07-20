// ===========================
// Navigation
// ===========================

export function createNavigation(categories) {

    const nav = document.getElementById("category-nav");

    nav.innerHTML = "";

    categories.forEach(category => {

        const button = document.createElement("button");

        button.className = "nav-button";
        button.textContent = category;

        button.addEventListener("click", () => {

            document
                .getElementById(`category-${category}`)
                ?.scrollIntoView({
                    behavior: "smooth"
                });

        });

        nav.appendChild(button);

    });

}

// ===========================
// Active Navigation
// ===========================

export function initNavigationObserver() {

    const buttons = document.querySelectorAll(".nav-button");
    const sections = document.querySelectorAll(".category");

    if (!buttons.length || !sections.length) {
        return;
    }

    const observer = new IntersectionObserver(entries => {

        entries.forEach(entry => {

            if (!entry.isIntersecting) {
                return;
            }

            const id = entry.target.id;

            buttons.forEach(button => {

                button.classList.toggle(
                    "active",
                    id === `category-${button.textContent}`
                );

            });

        });

    }, {
        threshold: 0.3
    });

    sections.forEach(section => {
        observer.observe(section);
    });

}
