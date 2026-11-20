
/* =================================
   HBNTORY - CLIENT WEB
   ================================= */

// 1. Récupération des éléments HTML

const questionForm = document.getElementById("question-form");
const questionInput = document.getElementById("question");
const responseArea = document.getElementById("response");

// 2. Adresse de l'AI Query Service

const API_URL = "http://127.0.0.1:5002/ask";

// 3. Écoute de la soumission du formulaire

questionForm.addEventListener("submit", async function (event) {

    // Empêche le rechargement automatique de la page
    event.preventDefault();

    // Récupère la question saisie
    const question = questionInput.value.trim();

    // Vérifie que la question n'est pas vide
    if (!question) {
        responseArea.textContent = "Veuillez saisir une question.";
        return;
    }

    // Affiche un message pendant le traitement
    responseArea.textContent = "Votre assistant réfléchit...";

    // Désactive le bouton pendant le traitement
    const submitButton = questionForm.querySelector("button");
    submitButton.disabled = true;

    try {

        // 4. Envoi de la question à l'AI Query Service

        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        // 5. Vérification de la réponse HTTP

        if (!response.ok) {
            throw new Error("Le service IA a rencontré une erreur.");
        }

        // 6. Récupération de la réponse JSON

        const data = await response.json();

        // Vérification de la présence de la réponse
        if (typeof data.answer !== "string") {
            throw new Error("La réponse du service est invalide.");
        }

        // 7. Affichage de la réponse de l'IA

        responseArea.textContent = data.answer;

    } catch (error) {

        // 8. Gestion des erreurs

        console.error("Erreur :", error);

        responseArea.textContent =
            "Impossible de contacter l'assistant. Veuillez réessayer.";

    } finally {

        // 9. Réactive le bouton dans tous les cas

        submitButton.disabled = false;
    }
});
