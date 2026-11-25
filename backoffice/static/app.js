/* =================================
   HBNTORY - BACKOFFICE
   Toutes les règles de sécurité sont appliquées par le backend :
   cette page ne fait qu'afficher et envoyer des demandes.
   ================================= */

// 1. Mémoire de la page : utilisateur connecté et agences

const state = {
    user: null,
    branches: [],
};

// 2. Fonction commune pour appeler les routes du Backoffice
//    Le cookie de session est envoyé automatiquement par le navigateur.

async function api(path, method = "GET", body = null) {
    const options = { method: method, headers: {} };
    if (body !== null) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }

    const response = await fetch(path, options);

    let data = null;
    try {
        data = await response.json();
    } catch (error) {
        data = null;
    }

    if (!response.ok) {
        const message = data && data.error ? data.error : "Erreur " + response.status;
        throw new Error(message);
    }
    return data;
}

// 3. Petits outils d'affichage

function showMessage(text, type) {
    const box = document.getElementById("message");
    box.textContent = text;
    box.className = "message " + type;
}

function hideMessage() {
    document.getElementById("message").className = "message hidden";
}

function show(id) {
    document.getElementById(id).classList.remove("hidden");
}

function hide(id) {
    document.getElementById(id).classList.add("hidden");
}

function branchName(branchId) {
    const branch = state.branches.find((b) => b.id === branchId);
    return branch ? branch.name : "—";
}

// Crée une ligne de tableau. textContent affiche les données comme du texte,
// jamais comme du code : un nom piégé ne peut pas s'exécuter.
function addRow(tbody, cells) {
    const row = document.createElement("tr");
    for (const cell of cells) {
        const td = document.createElement("td");
        if (cell instanceof Node) {
            td.appendChild(cell);
        } else {
            td.textContent = cell;
        }
        row.appendChild(td);
    }
    tbody.appendChild(row);
}

function fillSelect(select, options) {
    select.replaceChildren();
    for (const item of options) {
        const option = document.createElement("option");
        option.value = item.value;
        option.textContent = item.label;
        select.appendChild(option);
    }
}

// 4. Connexion et déconnexion

async function startSession() {
    state.user = await api("/api/me");
    state.branches = await api("/api/branches");

    let info = "Connecté : " + state.user.username;
    if (state.user.role === "common_user") {
        info += " – Agence " + branchName(state.user.branch_id);
    } else {
        info += " – Administrateur";
    }
    document.getElementById("session-info").textContent = info;

    hide("login-section");
    show("session-bar");

    if (state.user.role === "admin") {
        show("admin-panel");
        await loadUsers();
    } else {
        show("user-panel");
        document.getElementById("branch-name").textContent = branchName(state.user.branch_id);
        await loadStock();
        await loadCatalog();
    }
}

function endSession() {
    state.user = null;
    hide("session-bar");
    hide("admin-panel");
    hide("user-panel");
    show("login-section");
}

document.getElementById("login-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    hideMessage();
    try {
        await api("/api/login", "POST", {
            username: document.getElementById("login-username").value.trim(),
            password: document.getElementById("login-password").value,
        });
        document.getElementById("login-form").reset();
        await startSession();
    } catch (error) {
        showMessage(error.message, "error");
    }
});

document.getElementById("logout-button").addEventListener("click", async function () {
    try {
        await api("/api/logout", "POST");
    } finally {
        endSession();
        showMessage("Vous êtes déconnecté.", "success");
    }
});

// 5. Espace utilisateur standard : le stock de son agence

async function loadStock() {
    const data = await api("/api/stock/products");
    const tbody = document.getElementById("stock-body");
    tbody.replaceChildren();

    if (data.product_api_available) {
        hide("api-warning");
    } else {
        show("api-warning");
    }

    if (data.products.length === 0) {
        addRow(tbody, ["Aucun produit en stock", "", "", ""]);
        return;
    }
    for (const product of data.products) {
        addRow(tbody, [
            product.name || "(nom indisponible)",
            product.sku || "—",
            product.product_id,
            product.available_quantity,
        ]);
    }
}

async function loadCatalog() {
    try {
        const catalog = await api("/api/products");
        const options = catalog.map((product) => ({
            value: product.product_id,
            label: product.name + " (" + product.sku + ")" + (product.discontinued ? " – arrêté" : ""),
        }));
        fillSelect(document.getElementById("stock-product"), options);
        fillSelect(document.getElementById("check-product"), options);
    } catch (error) {
        showMessage("Catalogue indisponible : " + error.message, "error");
    }
}

async function changeStock(action) {
    hideMessage();
    const productId = Number(document.getElementById("stock-product").value);
    const quantity = Number(document.getElementById("stock-quantity").value);

    if (!Number.isInteger(quantity) || quantity <= 0) {
        showMessage("Indiquez une quantité entière et positive.", "error");
        return;
    }
    try {
        const result = await api("/api/stock/" + action, "POST", {
            product_id: productId,
            quantity: quantity,
        });
        const verb = action === "add" ? "ajouté" : "retiré";
        showMessage("Stock " + verb + ". Nouvelle quantité : " + result.available_quantity + ".", "success");
        document.getElementById("stock-quantity").value = "";
        await loadStock();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

document.getElementById("add-button").addEventListener("click", function () {
    changeStock("add");
});

document.getElementById("remove-button").addEventListener("click", function () {
    changeStock("remove");
});

document.getElementById("check-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    hideMessage();
    const select = document.getElementById("check-product");
    try {
        const result = await api("/api/stock/" + select.value);
        const label = select.options[select.selectedIndex].textContent;
        const box = document.getElementById("check-result");
        box.textContent = label + " : " + result.available_quantity + " en stock à " + branchName(result.branch_id) + ".";
        show("check-result");
    } catch (error) {
        showMessage(error.message, "error");
    }
});

// 6. Espace admin : la gestion des utilisateurs

async function loadUsers() {
    const users = await api("/api/users");
    const tbody = document.getElementById("users-body");
    tbody.replaceChildren();

    for (const user of users) {
        const badge = document.createElement("span");
        badge.className = "badge " + (user.is_active ? "badge-active" : "badge-inactive");
        badge.textContent = user.is_active ? "Actif" : "Désactivé";

        addRow(tbody, [
            user.id,
            user.username,
            user.role === "admin" ? "Admin" : "Utilisateur",
            user.branch_id ? branchName(user.branch_id) : "—",
            badge,
        ]);
    }

    // Seuls les utilisateurs standards actifs peuvent être modifiés
    const editable = users
        .filter((user) => user.role === "common_user" && user.is_active)
        .map((user) => ({
            value: user.id,
            label: user.username + " (" + branchName(user.branch_id) + ")",
        }));
    fillSelect(document.getElementById("edit-user"), editable);

    const branchOptions = state.branches.map((branch) => ({ value: branch.id, label: branch.name }));
    fillSelect(document.getElementById("create-branch"), branchOptions);
    fillSelect(document.getElementById("edit-branch"), branchOptions);
}

function selectedUserId() {
    const value = document.getElementById("edit-user").value;
    if (!value) {
        showMessage("Aucun utilisateur à modifier.", "error");
        return null;
    }
    return value;
}

document.getElementById("create-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    hideMessage();
    try {
        const user = await api("/api/users", "POST", {
            username: document.getElementById("create-username").value.trim(),
            password: document.getElementById("create-password").value,
            branch_id: Number(document.getElementById("create-branch").value),
        });
        showMessage("Utilisateur « " + user.username + " » créé.", "success");
        document.getElementById("create-form").reset();
        await loadUsers();
    } catch (error) {
        showMessage(error.message, "error");
    }
});

document.getElementById("branch-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    hideMessage();
    const userId = selectedUserId();
    if (!userId) {
        return;
    }
    try {
        await api("/api/users/" + userId + "/branch", "PUT", {
            branch_id: Number(document.getElementById("edit-branch").value),
        });
        showMessage("Agence modifiée.", "success");
        await loadUsers();
    } catch (error) {
        showMessage(error.message, "error");
    }
});

document.getElementById("password-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    hideMessage();
    const userId = selectedUserId();
    if (!userId) {
        return;
    }
    try {
        await api("/api/users/" + userId + "/password", "PUT", {
            password: document.getElementById("edit-password").value,
        });
        showMessage("Mot de passe modifié.", "success");
        document.getElementById("password-form").reset();
    } catch (error) {
        showMessage(error.message, "error");
    }
});

document.getElementById("deactivate-button").addEventListener("click", async function () {
    hideMessage();
    const userId = selectedUserId();
    if (!userId) {
        return;
    }
    if (!confirm("Désactiver cet utilisateur ? Il ne pourra plus se connecter.")) {
        return;
    }
    try {
        await api("/api/users/" + userId, "DELETE");
        showMessage("Utilisateur désactivé.", "success");
        await loadUsers();
    } catch (error) {
        showMessage(error.message, "error");
    }
});

// 7. Au chargement : si une session existe déjà, on l'affiche directement

startSession().catch(function () {
    endSession();
});
