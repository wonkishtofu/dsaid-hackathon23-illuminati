let ctx = document.getElementById("chart").getContext('2d');

// placeholder data, to be replaced with output from PVWatts API Call
var data_y = [4.11, 4.00, 3.02, 2.27, 1.54, 1.35, 1.54, 1.87, 2.72, 3.23, 3.27, 3.46]
var data_x = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
var units = "kWh/m²/day"

var gradientStroke = ctx.createLinearGradient(500, 0, 100, 0);
gradientStroke.addColorStop(0, "#ff6c00");
gradientStroke.addColorStop(1, "#d3183a");

var gradientBkgrd = ctx.createLinearGradient(0, 100, 0, 400);
gradientBkgrd.addColorStop(0, "rgba(244,94,132,0.2)");
gradientBkgrd.addColorStop(1, "rgba(249,135,94,0)");

let draw = Chart.controllers.line.prototype.draw;
Chart.controllers.line = Chart.controllers.line.extend({
    draw: function() {
        draw.apply(this, arguments);
        let ctx = this.chart.chart.ctx;
        let _stroke = ctx.stroke;
        ctx.stroke = function() {
            ctx.save();
            ctx.shadowBlur = 8;
            ctx.shadowOffsetX = 0;
            ctx.shadowOffsetY = 6;
            _stroke.apply(this, arguments)
            ctx.restore();
        }
    }
});

var chart = new Chart(ctx, {
    // The type of chart we want to create
    type: 'line',
    // The data for our dataset
    data: {
        labels: data_x,
        datasets: [{
            label: units,
            backgroundColor: gradientBkgrd,
            borderColor: gradientStroke,
            data: data_y,
            pointBorderColor: "rgba(255,255,255,0)",
            pointBackgroundColor: "rgb(247,180,45)",
            pointBorderWidth: 0,
            pointHoverRadius: 8,
            pointHoverBackgroundColor: gradientStroke,
            pointHoverBorderColor: "rgb(247,180,45)",
            pointHoverBorderWidth: 4,
            pointRadius: 1,
            borderWidth: 5,
            pointHitRadius: 16,
        }]
    },

    // Configuration options go here
    options: {
      tooltips: {
        backgroundColor:'#fff',
        displayColors: false,
           titleFontColor: '#000',
        bodyFontColor: '#000',
        titleFontSize: 24,
        bodyFontSize: 18,
        },
      legend: {
            display: false
      },
        scales: {
            xAxes: [{
                gridLines: {
                    display:false
                },
            }],
            yAxes: [{
              display: true,
              ticks: {
                suggestedMin: 0,    // minimum will be 0, unless there is a lower value.
                // OR //
                beginAtZero: true   // minimum value will be 0.
            }
        }]
        }
    }
});
