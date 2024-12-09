// Preparar modal según el tipo de entidad (Empresa o Banco)
function prepararModal(tipo) {
  document.getElementById("modalEntidadLabel").innerText =
    tipo === "empresa" ? "Agregar Empresa" : "Agregar Banco";
  document.getElementById("tipoEntidad").value =
    tipo === "empresa" ? "Empresa" : "Banco";
}

// Guardar la entidad en el servidor
function guardarEntidad() {
  const tipoEntidad = document.getElementById("tipoEntidad").value;
  const rut = document.getElementById("rut").value;
  const nombre = document.getElementById("nombre").value;

  fetch("/agregar_entidad", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      rut: rut,
      nombre: nombre,
      tipo_entidad: tipoEntidad,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert(`${tipoEntidad} agregada exitosamente!`);
        const select =
          tipoEntidad === "Empresa"
            ? document.getElementById("nombre_empresa")
            : document.getElementById("nombre_banco");

        // Agregar la nueva opción al select
        const option = document.createElement("option");
        option.value = data.id;
        option.textContent = nombre;
        select.appendChild(option);

        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("modalEntidad")
        );
        modal.hide();

        // Limpiar formulario
        document.getElementById("formEntidad").reset();
      } else {
        alert("Error al guardar la entidad: " + data.error);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Ocurrió un error al guardar la entidad.");
    });
}
