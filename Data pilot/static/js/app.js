const saleForm = document.getElementById("sale-form");
const saleMessage = document.getElementById("sale-message");
const saveSaleButton = document.getElementById("save-sale");

const questionForm = document.getElementById("question-form");
const questionInput = document.getElementById("business-question");
const questionMessage = document.getElementById("question-message");
const askButton = document.getElementById("ask-button");

const answerPanel = document.getElementById("answer-panel");
const answerText = document.getElementById("answer-text");
const answerModel = document.getElementById("answer-model");

const insightList = document.getElementById("insight-list");


async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("The server returned an invalid response.");
    }

    if (!response.ok) {
        throw new Error(
            data.error || "The request could not be completed."
        );
    }

    return data;
}


function showMessage(element, message, isError = false) {
    element.textContent = message;
    element.classList.toggle("error", isError);
}


function makeHistoryCard(item) {
    const card = document.createElement("article");
    card.className = "insight-card";

    const meta = document.createElement("div");
    meta.className = "insight-meta";

    const label = document.createElement("span");
    label.textContent = "Saved analysis";

    const time = document.createElement("time");
    time.textContent = item.created_at || "Just now";

    meta.append(label, time);

    const question = document.createElement("h3");
    question.textContent = item.question;

    const answer = document.createElement("p");
    answer.textContent = item.answer;

    card.append(meta, question, answer);

    return card;
}


function addInsightToHistory(item) {
    const empty = document.getElementById("insight-empty");

    if (empty) {
        empty.remove();
    }

    insightList.prepend(makeHistoryCard(item));

    const cards = insightList.querySelectorAll(".insight-card");

    cards.forEach((card, index) => {
        if (index >= 8) {
            card.remove();
        }
    });
}


saleForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const productName =
        document.getElementById("product-name").value.trim();

    const category =
        document.getElementById("category").value.trim();

    const quantity = Number(
        document.getElementById("quantity").value
    );

    const unitPrice = Number(
        document.getElementById("unit-price").value
    );

    const saleDate =
        document.getElementById("sale-date").value;

    if (!Number.isInteger(quantity) || quantity < 1) {
        showMessage(
            saleMessage,
            "Enter a valid whole-number quantity.",
            true
        );
        return;
    }

    if (!Number.isFinite(unitPrice) || unitPrice <= 0) {
        showMessage(
            saleMessage,
            "Enter a valid positive unit price.",
            true
        );
        return;
    }

    saveSaleButton.disabled = true;
    saveSaleButton.textContent = "Saving...";

    showMessage(saleMessage, "Saving the sale record.");

    try {
        await apiRequest("/api/sales", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                product_name: productName,
                category: category,
                quantity: quantity,
                unit_price: unitPrice,
                sale_date: saleDate
            })
        });

        showMessage(
            saleMessage,
            "Sale saved. Updating the dashboard."
        );

        window.location.reload();

    } catch (error) {
        showMessage(saleMessage, error.message, true);

        saveSaleButton.disabled = false;
        saveSaleButton.textContent = "Save sale";
    }
});


document.querySelectorAll("[data-question]").forEach((button) => {
    button.addEventListener("click", () => {
        questionInput.value = button.dataset.question || "";
        questionInput.focus();
    });
});


questionForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
        questionInput.focus();
        return;
    }

    answerPanel.hidden = false;

    answerText.textContent = "Analyzing your business data...";
    answerModel.textContent = "Working";
    askButton.disabled = true;
    askButton.textContent = "Analyzing...";

    showMessage(questionMessage, "");

    try {
        const data = await apiRequest("/api/ask", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })
        });

        answerText.textContent = data.answer;
        answerModel.textContent = data.model;

        if (data.insight) {
            addInsightToHistory(data.insight);
        }

    } catch (error) {
        answerText.textContent = error.message;
        answerModel.textContent = "Request failed";

        showMessage(questionMessage, error.message, true);

        console.error("DataPilot request failed:", error);

    } finally {
        askButton.disabled = false;
        askButton.textContent = "Analyze question";
    }
});


document.getElementById("sales-table-body").addEventListener(
    "click",
    async (event) => {
        const button = event.target.closest("[data-action='delete-sale']");

        if (!button) {
            return;
        }

        const row = button.closest("[data-sale-id]");

        if (!row) {
            return;
        }

        const confirmed = window.confirm(
            `Delete this sale for "${row.dataset.productName}"?`
        );

        if (!confirmed) {
            return;
        }

        button.disabled = true;
        button.textContent = "Deleting";

        try {
            await apiRequest(
                `/api/sales/${encodeURIComponent(row.dataset.saleId)}`,
                {
                    method: "DELETE"
                }
            );

            window.location.reload();

        } catch (error) {
            button.disabled = false;
            button.textContent = "Delete";

            window.alert(error.message);
        }
    }
);