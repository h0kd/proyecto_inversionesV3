function toggleRenovableFields() {
  const tipo = document.getElementById("tipo").value;
  const renovableFields = document.getElementById("renovable-fields");
  renovableFields.style.display = tipo === "Renovable" ? "block" : "none";
}

// Mostrar/ocultar campos según el valor inicial del tipo
document.addEventListener("DOMContentLoaded", toggleRenovableFields);
