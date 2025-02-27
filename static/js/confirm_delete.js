document.addEventListener("DOMContentLoaded", function () {
    let confirmInput = document.getElementById("confirmInput");
    let confirmButton = document.getElementById("confirmDeleteButton");
    let deleteForm = null;

    confirmInput.addEventListener("input", function () {
        if (confirmInput.value.trim() === "Eliminar") {
            confirmButton.removeAttribute("disabled");
        } else {
            confirmButton.setAttribute("disabled", "true");
        }
    });

    // Detectar cuál botón de eliminación fue presionado
    document.querySelectorAll(".delete-button").forEach(button => {
        button.addEventListener("click", function () {
            deleteForm = document.getElementById(this.getAttribute("data-form-id"));
            confirmButton.setAttribute("data-form-id", this.getAttribute("data-form-id"));
        });
    });

    // Confirmar la eliminación al hacer clic en el botón dentro del modal
    confirmButton.addEventListener("click", function () {
        if (deleteForm) {
            deleteForm.submit();
        }
    });
});
