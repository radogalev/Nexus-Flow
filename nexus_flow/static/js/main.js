document.addEventListener("DOMContentLoaded", () => {
  const addBtn = document.getElementById("add-service-row");
  if (addBtn) {
    addBtn.addEventListener("click", () => {
      const totalForms = document.getElementById("id_contractservice_set-TOTAL_FORMS");
      const rows = document.querySelectorAll(".contract-service-row");
      if (!totalForms || rows.length === 0) {
        return;
      }

      const newIndex = parseInt(totalForms.value, 10);
      const clone = rows[rows.length - 1].cloneNode(true);
      clone.querySelectorAll("input, select, textarea").forEach((el) => {
        el.name = el.name.replace(/-(\d+)-/, `-${newIndex}-`);
        el.id = el.id.replace(/-(\d+)-/, `-${newIndex}-`);
        if (el.type !== "hidden" && el.type !== "checkbox") {
          el.value = "";
        }
        if (el.type === "checkbox") {
          el.checked = false;
        }
      });
      rows[rows.length - 1].parentElement.appendChild(clone);
      totalForms.value = newIndex + 1;
    });
  }

  const avatarInput = document.getElementById("id_avatar");
  const avatarPreview = document.getElementById("avatar-preview");
  if (avatarInput && avatarPreview) {
    avatarInput.addEventListener("change", (event) => {
      const file = event.target.files?.[0];
      if (!file) {
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        avatarPreview.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  document.querySelectorAll(".alert").forEach((alert) => {
    setTimeout(() => {
      alert.classList.add("fade");
    }, 4000);
  });
});
