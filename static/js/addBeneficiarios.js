function guardarBeneficiario() {
  const tipoBeneficiario = document.getElementById(
    "tipo_beneficiario_modal"
  ).value;
  const nombre = document.getElementById("nombre_beneficiario_modal").value;
  const rut = document.getElementById("rut_beneficiario_modal").value;

  if (!tipoBeneficiario || !nombre || !rut) {
    alert("Por favor, complete todos los campos.");
    return;
  }

  fetch("/agregar_beneficiario", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      tipo_beneficiario: tipoBeneficiario,
      nombre: nombre,
      rut: rut,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert("Beneficiario agregado exitosamente!");

        // Agregar el nuevo beneficiario al select
        const selectBeneficiario = document.getElementById(
          "nombre_beneficiario"
        );
        const option = document.createElement("option");
        option.value = data.id;
        option.textContent = nombre;
        selectBeneficiario.appendChild(option);

        // Cerrar el modal
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("addBeneficiarioModal")
        );
        modal.hide();

        // Limpiar el formulario del modal
        document.getElementById("formBeneficiario").reset();
      } else {
        alert("Error al guardar el beneficiario: " + data.error);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Ocurrió un error al guardar el beneficiario.");
    });
}

function guardarBanco(event) {
  // Prevenir el envío predeterminado del formulario
  if (event) event.preventDefault();

  const rutBanco = document.getElementById("rut_banco_modal").value;
  const nombreBanco = document.getElementById("nombre_banco_modal").value;

  if (!rutBanco || !nombreBanco) {
    alert("Por favor, complete todos los campos.");
    return;
  }

  fetch("/agregar_banco", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      rut: rutBanco,
      nombre: nombreBanco,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert("Banco agregado exitosamente!");

        // Agregar el nuevo banco al select
        const selectBanco = document.getElementById("nombre_banco");
        const option = document.createElement("option");
        option.value = data.id;
        option.textContent = nombreBanco;
        selectBanco.appendChild(option);

        // Seleccionar automáticamente el nuevo banco
        selectBanco.value = data.id;

        // Cerrar el modal
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("addBancoModal")
        );
        modal.hide();

        // Limpiar el formulario del modal
        document.getElementById("formBanco").reset();
      } else {
        alert("Error al guardar el banco: " + data.error);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Ocurrió un error al guardar el banco.");
    });
}
