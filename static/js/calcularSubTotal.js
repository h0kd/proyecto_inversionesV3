// Calcular SubTotal automáticamente
function calcularSubtotal() {
  const cantidad = parseFloat(document.getElementById("cantidad").value) || 0;
  const precioUnitario =
    parseFloat(document.getElementById("precio_unitario").value) || 0;
  const subtotal = cantidad * precioUnitario;
  document.getElementById("subtotal").value = subtotal.toFixed(2);
}
