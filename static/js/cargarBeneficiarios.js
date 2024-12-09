function cargarBeneficiarios() {
  const tipoBeneficiario = document.getElementById("tipo_beneficiario").value;
  const selectBeneficiario = document.getElementById("nombre_beneficiario");
  const rutBeneficiario = document.getElementById("rut_beneficiario");

  // Limpiar los select
  selectBeneficiario.innerHTML =
    '<option value="" disabled selected>Cargando...</option>';
  rutBeneficiario.value = "";

  // Hacer una solicitud al servidor para obtener los beneficiarios
  fetch(`/beneficiarios_por_tipo/${tipoBeneficiario}`)
    .then((response) => response.json())
    .then((data) => {
      selectBeneficiario.innerHTML =
        '<option value="" disabled selected>Seleccione un beneficiario</option>';
      data.forEach((beneficiario) => {
        const option = document.createElement("option");
        option.value = beneficiario.id; // ID del beneficiario
        option.textContent = beneficiario.nombre;
        option.dataset.rut = beneficiario.rut; // Guardar el RUT en un atributo de datos
        selectBeneficiario.appendChild(option);
      });
    })
    .catch((error) => {
      console.error("Error al cargar beneficiarios:", error);
      selectBeneficiario.innerHTML =
        '<option value="" disabled selected>Error al cargar</option>';
    });

  // Actualizar el campo RUT cuando se seleccione un beneficiario
  selectBeneficiario.addEventListener("change", function () {
    const selectedOption = this.options[this.selectedIndex];
    rutBeneficiario.value = selectedOption.dataset.rut || ""; // Establecer el RUT seleccionado
  });
}
