document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".code-preview").forEach(preview => {
    // Create toggle button
    const btn = document.createElement("button");
    btn.className = "code-preview-toggle";
    btn.textContent = "Show more";

    // Toggle logic
    btn.addEventListener("click", () => {
      preview.classList.toggle("expanded");
      btn.textContent = preview.classList.contains("expanded")
        ? "Show less"
        : "Show more";
    });

    // Insert button after the preview block
    preview.insertAdjacentElement("afterend", btn);
  });
});
