// Fetch waste type for tomorrow
document.addEventListener("DOMContentLoaded", async () => {
    const wasteTypeElement = document.getElementById("wasteType");

    const response = await fetch("http://localhost:5000/api/users/get-waste-type");
    const data = await response.json();
    wasteTypeElement.textContent = data.wasteType || "Unknown Waste";
});

// Mark waste availability
async function markWaste(status) {
    const wasteAvailable = status === "have";

    const response = await fetch("http://localhost:5000/api/users/mark-waste", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId: "1001", wasteAvailable }) // Replace with logged-in user ID
    });

    const data = await response.json();
    if (data.success) {
        alert(`You have successfully marked "${status === 'have' ? 'Have Waste' : 'Do not Have Waste'}".`);
    } else {
        alert("Error marking waste status. Please try again.");
    }
}
