const registeredVehicleNo = "123456";

document.getElementById("login-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const enteredVehicleNo = document.getElementById("vehicleNo").value;
    if (enteredVehicleNo === registeredVehicleNo) {
        window.location.href = "../MapPage/MapPage.html"; // Redirect to the map page
    } else {
        alert("Invalid Vehicle Number. Please try again.");
    }
});
