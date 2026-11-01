const welcome = document.getElementById("welcome");
const registration = document.getElementById("registration");
const dashboard = document.getElementById("dashboard");
const symptomSection = document.getElementById("symptomSection");
const chatSection = document.getElementById("chatSection");
const resultsSection = document.getElementById("analysisResults");

function showOnly(section) {
    [welcome, registration, dashboard, symptomSection, chatSection]
        .forEach(item => item.classList.add("hidden"));
    section.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function showRegistration() {
    showOnly(registration);
}

function showDashboard() {
    showOnly(dashboard);
}

document.getElementById("profileForm").addEventListener("submit", function(event) {
    event.preventDefault();
    const name = document.getElementById("name").value.trim();
    const age = Number(document.getElementById("age").value);
    const gender = document.getElementById("gender").value;

    if (!name || !Number.isInteger(age) || age < 1 || age > 120) {
        alert("Please enter a valid name and age.");
        return;
    }

    sessionStorage.setItem("medimindProfile", JSON.stringify({ name, age, gender }));
    document.getElementById("userName").textContent = name;
    showOnly(dashboard);
});

function startAssessment() {
    resultsSection.classList.add("hidden");
    showOnly(symptomSection);
}

function openChat() {
    showOnly(chatSection);
    document.getElementById("chatInput").focus();
}

function addText(parent, tag, content, className = "") {
    const element = document.createElement(tag);
    element.textContent = content;
    if (className) element.className = className;
    parent.appendChild(element);
    return element;
}

function createList(parent, items) {
    const list = document.createElement("ul");
    items.forEach(item => addText(list, "li", item));
    parent.appendChild(list);
}

function displayResults(result, selectedSymptoms, description) {
    resultsSection.replaceChildren();
    resultsSection.classList.remove("hidden");

    const heading = document.createElement("div");
    heading.className = "results-heading";
    addText(heading, "h2", "Your Health Information Report");
    addText(heading, "p", "Educational information based on the symptoms you entered.");
    resultsSection.appendChild(heading);

    const selectedBlock = document.createElement("div");
    selectedBlock.className = "result-block";
    addText(selectedBlock, "h3", "Selected Symptoms");
    addText(selectedBlock, "p", selectedSymptoms.length ? selectedSymptoms.join(", ") : "No listed symptoms selected.");
    if (description) addText(selectedBlock, "p", "Additional description: " + description);
    resultsSection.appendChild(selectedBlock);

    const conditionsBlock = document.createElement("div");
    conditionsBlock.className = "result-block";
    addText(conditionsBlock, "h3", "Possible Conditions to Discuss");

    (result.possible_conditions || []).forEach(condition => {
        const card = document.createElement("article");
        card.className = "condition-card";
        addText(card, "h4", condition.name);
        addText(card, "p", condition.reason);
        addText(card, "p", "Tests or assessments to discuss with a clinician:");
        createList(card, condition.tests_to_discuss || []);
        conditionsBlock.appendChild(card);
    });
    resultsSection.appendChild(conditionsBlock);

    const adviceBlock = document.createElement("div");
    adviceBlock.className = "result-block";
    addText(adviceBlock, "h3", "General Health Information");
    createList(adviceBlock, result.general_advice || []);
    resultsSection.appendChild(adviceBlock);

    const disclaimer = document.createElement("div");
    disclaimer.className = "medical-disclaimer";
    addText(disclaimer, "strong", "Important Medical Information");
    addText(disclaimer, "p", result.disclaimer || "This is educational information, not a diagnosis.");
    addText(disclaimer, "p", "Seek urgent medical care for severe or rapidly worsening symptoms.");
    resultsSection.appendChild(disclaimer);

    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

document.getElementById("symptomForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const selectedSymptoms = Array.from(
        document.querySelectorAll(".symptom-options input:checked")
    ).map(item => item.value);
    const description = document.getElementById("symptomDescription").value.trim();

    if (selectedSymptoms.length === 0 && !description) {
        alert("Please select or describe at least one symptom.");
        return;
    }

    const button = document.getElementById("analyzeButton");
    button.disabled = true;
    button.textContent = "Preparing your report...";

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symptoms: selectedSymptoms, description })
        });
        const result = await response.json();

        if (!response.ok) throw new Error(result.error || "Unable to process the request.");
        if (!Array.isArray(result.possible_conditions)) throw new Error("Unexpected analyzer response.");

        displayResults(result, selectedSymptoms, description);
    } catch (error) {
        console.error(error);
        alert("Unable to generate the report. Check that the server is running and try again.");
    } finally {
        button.disabled = false;
        button.textContent = "Explore Health Information →";
    }
});

/* CHATBOT */
const chatHistory = [];
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendChatButton = document.getElementById("sendChatButton");
const chatStatus = document.getElementById("chatStatus");

function addChatBubble(role, text) {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble " + role;
    const label = role === "user" ? "You" : "MediMind AI";
    addText(bubble, "strong", label);
    addText(bubble, "p", text);
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return bubble;
}

async function checkOllama() {
    const status = document.getElementById("chatModelStatus");
    try {
        const response = await fetch("/models");
        const data = await response.json();
        if (!response.ok || !data.available) {
            status.textContent = "Local AI model unavailable. Check Ollama.";
            status.classList.add("status-error");
            return;
        }
        status.textContent = "Ready · " + data.model;
        status.classList.remove("status-error");
    } catch (error) {
        status.textContent = "Could not connect to local AI.";
        status.classList.add("status-error");
    }
}

chatForm.addEventListener("submit", async function(event) {
    event.preventDefault();
    const message = chatInput.value.trim();

    if (!message) return;
    if (message.length > 1200) {
        chatStatus.textContent = "Please keep your message under 1,200 characters.";
        return;
    }

    addChatBubble("user", message);
    chatInput.value = "";
    sendChatButton.disabled = true;
    sendChatButton.textContent = "Thinking...";
    chatStatus.textContent = "MediMind AI is preparing a response...";

    const historyForRequest = chatHistory.slice(-8);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                history: historyForRequest
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Chat request failed.");

        addChatBubble("assistant", data.reply);
        chatHistory.push(
            { role: "user", content: message },
            { role: "assistant", content: data.reply }
        );
        chatStatus.textContent = "Connected to local model: " + data.model;
    } catch (error) {
        addChatBubble("assistant", error.message);
        chatStatus.textContent = "Check that Ollama is running and a model is installed.";
    } finally {
        sendChatButton.disabled = false;
        sendChatButton.textContent = "Send ↑";
        chatInput.focus();
    }
});

checkOllama();


/* HEALTH PROFILE AND RECORDS */
const healthProfileSection = document.getElementById("healthProfileSection");
const healthProfileFields = [
    "full_name", "date_of_birth", "gender", "blood_group", "height", "weight",
    "emergency_contact", "conditions", "allergies", "surgeries", "family_history",
    "current_medicines", "hospitalisations"
];
const profileFieldIds = {
    full_name: "hp_full_name", date_of_birth: "hp_dob", gender: "hp_gender",
    blood_group: "hp_blood_group", height: "hp_height", weight: "hp_weight",
    emergency_contact: "hp_emergency_contact", conditions: "hp_conditions",
    allergies: "hp_allergies", surgeries: "hp_surgeries",
    family_history: "hp_family_history", current_medicines: "hp_current_medicines",
    hospitalisations: "hp_hospitalisations"
};

async function openHealthProfile() {
    showOnly(healthProfileSection);
    await loadHealthProfile();
    await loadHealthRecords();
}

async function loadHealthProfile() {
    try {
        const response = await fetch("/profile");
        const data = await response.json();
        healthProfileFields.forEach(field => {
            document.getElementById(profileFieldIds[field]).value = data[field] || "";
        });
    } catch (error) {
        document.getElementById("profileSaveStatus").textContent = "Could not load profile.";
    }
}

document.getElementById("healthProfileForm").addEventListener("submit", async event => {
    event.preventDefault();
    const data = {};
    healthProfileFields.forEach(field => {
        data[field] = document.getElementById(profileFieldIds[field]).value.trim();
    });
    const status = document.getElementById("profileSaveStatus");
    status.textContent = "Saving...";
    try {
        const response = await fetch("/profile", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not save.");
        status.textContent = "Saved on this computer.";
        document.getElementById("userName").textContent = data.full_name;
    } catch (error) {
        status.textContent = error.message;
    }
});

async function loadHealthRecords() {
    const list = document.getElementById("healthRecordsList");
    list.textContent = "Loading records...";
    try {
        const response = await fetch("/records");
        const records = await response.json();
        await loadHealthOverview();
        list.replaceChildren();
        if (!records.length) {
            list.textContent = "No health records saved yet.";
            return;
        }
        records.forEach(record => {
            const card = document.createElement("article");
            card.className = "saved-record";
            const title = document.createElement("strong");
            title.textContent = record.record_type === "upload"
                ? (record.original_filename || "Uploaded report")
                : record.test_name;
            card.appendChild(title);
            const detail = document.createElement("p");
            detail.textContent = record.record_type === "upload"
                ? "Uploaded report · " + (record.record_date || "Date not entered")
                : "Result: " + record.result + (record.unit ? " " + record.unit : "") +
                  (record.reference_range ? " · Reference range: " + record.reference_range : "") +
                  " · " + (record.record_date || "Date not entered");
            card.appendChild(detail);
            if (record.notes) {
                const note = document.createElement("p");
                note.textContent = "Notes: " + record.notes;
                card.appendChild(note);
            }
            if (record.record_type === "upload") {
                const view = document.createElement("a");
                view.href = "/records/file/" + record.id;
                view.textContent = "Download report";
                view.className = "record-link";
                card.appendChild(view);
            }
            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "record-delete";
            remove.textContent = "Delete";
            remove.addEventListener("click", async () => {
                if (!confirm("Delete this health record permanently?")) return;
                const deleted = await fetch("/records/" + record.id, {method: "DELETE"});
                if (deleted.ok) loadHealthRecords();
                else alert("Could not delete this record.");
            });
            card.appendChild(remove);
            list.appendChild(card);
        });
    } catch (error) {
        list.textContent = "Could not load saved records.";
    }
}

document.getElementById("manualRecordForm").addEventListener("submit", async event => {
    event.preventDefault();
    const form = new FormData();
    form.append("record_type", "manual");
    form.append("test_name", document.getElementById("record_test_name").value.trim());
    form.append("result", document.getElementById("record_result").value.trim());
    form.append("unit", document.getElementById("record_unit").value.trim());
    form.append("reference_range", document.getElementById("record_range").value.trim());
    form.append("record_date", document.getElementById("record_date").value);
    form.append("notes", document.getElementById("record_notes").value.trim());
    try {
        const response = await fetch("/records", {method: "POST", body: form});
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not save result.");
        event.target.reset();
        await loadHealthRecords();
        alert("Test result saved.");
    } catch (error) {
        alert(error.message);
    }
});

document.getElementById("uploadRecordForm").addEventListener("submit", async event => {
    event.preventDefault();
    const fileInput = document.getElementById("report_file");
    if (!fileInput.files.length) return;
    const form = new FormData();
    form.append("record_type", "upload");
    form.append("report", fileInput.files[0]);
    form.append("record_date", document.getElementById("upload_date").value);
    form.append("notes", document.getElementById("upload_notes").value.trim());
    try {
        const response = await fetch("/records", {method: "POST", body: form});
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not upload report.");
        event.target.reset();
        await loadHealthRecords();
        alert("Report uploaded.");
    } catch (error) {
        alert(error.message);
    }
});


async function loadHealthOverview() {
    const timeline = document.getElementById("healthTimeline");
    try {
        const response = await fetch("/dashboard-summary");
        const data = await response.json();
        document.getElementById("statTotal").textContent = data.total_records;
        document.getElementById("statUploads").textContent = data.uploaded_reports;
        document.getElementById("statManual").textContent = data.manual_results;
        timeline.replaceChildren();
        if (!data.recent_records.length) {
            timeline.textContent = "No saved activity yet. Add a test result or upload a report to begin.";
            return;
        }
        data.recent_records.forEach(record => {
            const item = document.createElement("div");
            item.className = "timeline-item";
            const dot = document.createElement("span");
            dot.className = "timeline-dot";
            const content = document.createElement("div");
            const title = document.createElement("strong");
            title.textContent = record.record_type === "upload"
                ? (record.original_filename || "Uploaded report")
                : (record.test_name || "Manual test result");
            const date = document.createElement("p");
            date.textContent = record.record_date || "Date not entered";
            content.append(title, date);
            item.append(dot, content);
            timeline.appendChild(item);
        });
    } catch (error) {
        timeline.textContent = "Health overview is temporarily unavailable.";
    }
}
