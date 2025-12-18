document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("img-modal");
  const modalImg = document.getElementById("modal-img");
  const closeBtn = document.querySelector("#img-modal .close-btn");

  // target any figure with class clickable-image
  document.querySelectorAll("figure.clickable-image img").forEach(img => {
    img.style.cursor = "zoom-in";  // or pointer, up to you
    img.addEventListener("click", () => {
      modal.style.display = "flex";
      modalImg.src = img.src;
    });
  });

  closeBtn.addEventListener("click", () => {
    modal.style.display = "none";
  });

  modal.addEventListener("click", e => {
    if (e.target === modal) modal.style.display = "none";
  });
});
