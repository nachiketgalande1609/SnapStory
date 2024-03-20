// Get the button and overlay elements
var viewImageBtn = document.getElementById("viewImageBtn");
var imageOverlay = document.getElementById("imageOverlay");

// When the button is clicked, display the image in the overlay
viewImageBtn.addEventListener("click", function() {
    imageOverlay.style.display = "flex";
});

// Close the overlay when the close button is clicked
function closeOverlay() {
    imageOverlay.style.display = "none";
}