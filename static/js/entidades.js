// entidades.js

// Función para cargar los nombres de las entidades según el tipo seleccionado
function cargarEntidades(tipo) {
  fetch(`/entidades_por_tipo/${tipo}`)
    .then((response) => response.json())
    .then((data) => {
      const nombreEntidadSelect = document.getElementById("nombre_entidad");
      nombreEntidadSelect.innerHTML =
        '<option value="" disabled selected>Seleccione una entidad</option>';
      data.forEach((entidad) => {
        const option = document.createElement("option");
        option.value = entidad.id;
        option.textContent = entidad.nombre;
        nombreEntidadSelect.appendChild(option);
      });
    })
    .catch((error) => console.error("Error al cargar las entidades:", error));
}
