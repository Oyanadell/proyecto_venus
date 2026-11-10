(() => {
    const initializeSidebar = () => {
        const sidebar = document.querySelector(".navbar-antonia");
        const header = sidebar?.firstElementChild;
        const navigation = sidebar?.children[1];

        if (!sidebar || !header || !navigation) {
            return;
        }

        navigation.id = "main-navigation";

        const shortLabels = {
            dashboard: "DA",
            reservas: "RE",
            clientes: "CL",
            servicios: "SE",
            "gestión de servicios": "GS",
            "registrar atención": "RA",
            "historial ventas": "HV",
            caja: "CA",
            inventario: "IN",
            personal: "PE",
        };
        navigation.querySelectorAll(".nav-link-antonia").forEach((link) => {
            const label = link.textContent.trim();
            link.dataset.short = shortLabels[label.toLocaleLowerCase("es")] || label.slice(0, 2).toUpperCase();
            link.title = label;
        });

        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "sidebar-toggle";
        toggle.setAttribute("aria-controls", navigation.id);
        header.appendChild(toggle);

        const setCollapsed = (collapsed) => {
            document.body.classList.toggle("sidebar-collapsed", collapsed);
            toggle.setAttribute("aria-expanded", String(!collapsed));
            toggle.setAttribute("aria-label", collapsed ? "Expandir menú" : "Minimizar menú");
            toggle.title = collapsed ? "Expandir menú" : "Minimizar menú";
            toggle.textContent = collapsed ? "›" : "‹";
            localStorage.setItem("sidebar-collapsed", String(collapsed));
        };

        toggle.addEventListener("click", () => {
            setCollapsed(!document.body.classList.contains("sidebar-collapsed"));
        });

        setCollapsed(localStorage.getItem("sidebar-collapsed") === "true");
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeSidebar);
    } else {
        initializeSidebar();
    }
})();
