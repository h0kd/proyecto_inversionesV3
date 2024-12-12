document.addEventListener("DOMContentLoaded", function () {
	// Asegúrate de que estas variables estén definidas en tu HTML
	const chartLabels = window.chartLabels || [];
	const chartData = window.chartData || [];

	const data = {
		labels: chartLabels,
		datasets: [
			{
				label: "Acciones Suma Total",
				data: chartData,
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
		data: data,
		options: {
			responsive: true,
			plugins: {
				legend: {
					position: "top",
				},
				title: {
					display: true,
					text: "Acciones Suma Total",
				},
			},
		},
	};

	// Renderizar el gráfico
	const accionesEmpresasChart = new Chart(
		document.getElementById("accionesEmpresasChart"),
		config
	);
});
