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
                "#4285f4", // Google Blue
                "#34a853", // Google Green
                "#fbbc04", // Google Yellow
                "#ea4335", // Google Red
                "#9c27b0", // Purple
                "#ff9800", // Orange
                "#00bcd4", // Cyan
                "#4caf50", // Light Green
                "#ff5722", // Deep Orange
                "#3f51b5", // Indigo
                "#e91e63", // Pink
                "#795548", // Brown
                "#607d8b", // Blue Grey
                "#8bc34a", // Light Green
                "#ffc107", // Amber
                "#9e9e9e", // Grey
                "#673ab7", // Deep Purple
                "#2196f3", // Blue
                "#ffeb3b", // Yellow
                "#f44336", // Red
                "#009688", // Teal
                "#cddc39", // Lime
                "#3f51b5", // Indigo
                "#ff4081", // Pink
                "#00bcd4", // Cyan
                "#4caf50", // Green
                "#ff9800", // Orange
                "#9c27b0", // Purple
                "#607d8b", // Blue Grey
                "#795548", // Brown
                "#e91e63", // Pink
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
