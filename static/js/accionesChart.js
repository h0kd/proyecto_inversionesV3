document.addEventListener("DOMContentLoaded", function () {
	// Configuración del gráfico
	const chartDataConfig = {
		labels: chartLabels, // Etiquetas desde el template
		datasets: [
			{
				label: "Total en Compras",
				data: chartDataset, // Datos desde el template
				backgroundColor: [
					"rgba(255, 99, 132, 0.6)",
					"rgba(54, 162, 235, 0.6)",
					"rgba(255, 206, 86, 0.6)",
					"rgba(75, 192, 192, 0.6)",
					"rgba(153, 102, 255, 0.6)",
					"rgba(255, 159, 64, 0.6)",
				],
				borderColor: [
					"rgba(255, 99, 132, 1)",
					"rgba(54, 162, 235, 1)",
					"rgba(255, 206, 86, 1)",
					"rgba(75, 192, 192, 1)",
					"rgba(153, 102, 255, 1)",
					"rgba(255, 159, 64, 1)",
				],
				borderWidth: 1,
			},
		],
	};

	const config = {
		type: "pie",
		data: chartDataConfig,
		options: {
			responsive: true,
			plugins: {
				legend: {
					position: "top",
				},
				title: {
					display: true,
					text: "Total en Compras por Empresa",
				},
			},
		},
	};

	// Renderizar el gráfico
	const accionesChart = new Chart(
		document.getElementById("accionesChart"),
		config
	);
});
