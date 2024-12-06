// Calcular Valor Total automáticamente
function calcularValortotal() {
  const cantidad = parseFloat(document.getElementById("cantidad").value) || 0;
  const precioUnitario =
    parseFloat(document.getElementById("precio_unitario").value) || 0;
  const comision = parseFloat(document.getElementById("comision").value) || 0;
  const gasto = parseFloat(document.getElementById("gasto").value) || 0;
  const subtotal = cantidad * precioUnitario;
  const iva = Math.round((comision + gasto) * 0.19);
  const valor_total = subtotal + iva + comision + gasto;
  document.getElementById("valor_total").value = valor_total.toFixed(2);
}
