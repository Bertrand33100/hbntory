/* =================================
   HBNTORY - ASSISTANT IA VIVANT
   ================================= */

const questionForm = document.getElementById("question-form");
const questionInput = document.getElementById("question");
const responseArea = document.getElementById("response");
const submitButton = questionForm.querySelector("button");

const API_URL = "http://127.0.0.1:5002/ask";

function wait(milliseconds) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}

async function revealAnswer(answer) {
  responseArea.className = "is-answer";

  const words = answer.split(/(\s+)/);
  let displayedText = "";

  for (const word of words) {
    displayedText += word;
    responseArea.textContent = displayedText;
    await wait(24);
  }
}

questionForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const question = questionInput.value.trim();

  if (!question) {
    responseArea.className = "is-error";
    responseArea.textContent = "Veuillez saisir une question.";
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "Réflexion...";
  questionInput.disabled = true;

  responseArea.className = "is-loading";
  responseArea.textContent = "HBntory réfléchit";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question,
      }),
    });

    if (!response.ok) {
      throw new Error("Erreur du service IA.");
    }

    const data = await response.json();

    if (typeof data.answer !== "string" || !data.answer.trim()) {
      throw new Error("Réponse invalide.");
    }

    await revealAnswer(data.answer.trim());
  } catch (error) {
    console.error("Erreur :", error);

    responseArea.className = "is-error";
    responseArea.textContent =
      "Impossible de contacter l'assistant. Vérifiez que les services sont démarrés, puis réessayez.";
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Envoyer";
    questionInput.disabled = false;
    questionInput.focus();
  }
});
