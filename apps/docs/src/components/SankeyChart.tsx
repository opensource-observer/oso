import React, { useEffect, useRef } from "react";

declare global {
  interface Window {
    google: any;
  }
}

interface SankeyChartProps {
  data: Array<[string, string, number]>;
  width?: number;
  height?: number;
}

export default function SankeyChart({
  data,
  width = 800,
  height = 600,
}: SankeyChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load Google Charts script if not already loaded
    const loadGoogleCharts = () => {
      if (window.google && window.google.charts) {
        return Promise.resolve();
      }

      return new Promise<void>((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://www.gstatic.com/charts/loader.js";
        script.onload = () => {
          window.google.charts.load("current", { packages: ["sankey"] });
          window.google.charts.setOnLoadCallback(() => resolve());
        };
        script.onerror = reject;
        document.head.appendChild(script);
      });
    };

    const drawChart = () => {
      if (!chartRef.current || !window.google) return;

      try {
        const chartData = new window.google.visualization.DataTable();
        chartData.addColumn("string", "From");
        chartData.addColumn("string", "To");
        chartData.addColumn("number", "Amount");
        chartData.addRows(data);

        const options = {
          width,
          height,
          sankey: {
            node: {
              width: 20,
              nodePadding: 10,
              colors: [
                "#4285f4",
                "#34a853",
                "#fbbc04",
                "#ea4335",
                "#9c27b0",
                "#ff9800",
              ],
            },
            link: {
              colorMode: "gradient",
              fillColor: "#e8f0fe",
            },
          },
          backgroundColor: "#ffffff",
        };

        const chart = new window.google.visualization.Sankey(chartRef.current);
        chart.draw(chartData, options);
      } catch {
        if (chartRef.current) {
          chartRef.current.innerHTML =
            '<p style="text-align: center; color: #666;">Chart loading...</p>';
        }
      }
    };

    // Only draw chart if we have data
    if (data.length > 0) {
      loadGoogleCharts()
        .then(drawChart)
        .catch(() => {
          if (chartRef.current) {
            chartRef.current.innerHTML =
              '<p style="text-align: center; color: #666;">Failed to load chart</p>';
          }
        });
    }
  }, [data, width, height]);

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        margin: "2rem 0",
        padding: "1rem",
        border: "1px solid #e1e4e8",
        borderRadius: "8px",
        backgroundColor: "#fafbfc",
      }}
    >
      <div
        ref={chartRef}
        style={{
          minHeight: `${height}px`,
          width: "100%",
          maxWidth: `${width}px`,
        }}
      />
    </div>
  );
}
