---
title: Tutorials
sidebar_position: 0
---

export const paths = {
quickstart: './quickstart/',
collectionView: './collection-view/',
projectDeepdive: './project-deepdive/',
mapDependencies: './dependencies/',
networkGraphs: './network-graph/',
developerRetention: '',
analyzeFunding: './funding-data/',
trustedUsers: '',
grantKpiDashboard: '',
cohortAnalysis: './cohort-analysis/',
uniswapHooks: './uniswap-hooks/',
forecasting: '',
openRank: '',
causalInference: '',
economicSimulationSandbox: '',
};

# Tutorials

Explore examples of applications and data science built on OSO's data platform. Each example includes code snippets you can copy and paste into your own projects.

---

### Start here

| Title                                          | Description                                                         |
| ---------------------------------------------- | ------------------------------------------------------------------- |
| 🌱 [Quickstart]({paths.quickstart})            | Learn the basics of `pyoso` and common query patterns               |
| 📊 [Collection View]({paths.collectionView})   | Get a high-level view of key metrics for any collection of projects |
| 🔬 [Project Deepdive]({paths.projectDeepdive}) | Drill into every facet of a single project                          |

---

### 👨‍💻 Open-Source Developers

Understand how your project is doing, explore contributions, and grow visibility

<div className="category-cards">
  <a href={paths.mapDependencies} className="mini-card">
    <h3>📦 Map Dependencies</h3>
    <p>Map software supply chains and package dependencies</p>
  </a>
  <a href={paths.networkGraphs} className="mini-card">
    <h3>🕸️ Network Graphs</h3>
    <p>Analyze collaboration patterns and community connections</p>
  </a>
  <div className="mini-card disabled">
    <h3>🤝 Developer Retention <em>(coming&nbsp;soon)</em></h3>
    <p>View developer churn and retention patterns over time</p>
  </div>
</div>

---

### 🏛️ Foundations & DAOs

Analyze funding impact, evaluate grantees, and monitor developer ecosystems

<div className="category-cards">
  <a href={paths.analyzeFunding} className="mini-card">
    <h3>💸 Analyze Funding</h3>
    <p>Track funding flows and analyze grant program impact</p>
  </a>
  <a href={paths.uniswapHooks} className="mini-card">
    <h3>🪝 Uniswap Hooks</h3>
    <p>Join OSO and Dune data to profile early Uniswap v4 hook adoption</p>
  </a>
  <div className="mini-card disabled">
    <h3>💻 Grant KPI Dashboard <em>(coming&nbsp;soon)</em></h3>
    <p>Build a live dashboard to track the progress and impact of grants</p>
  </div>
</div>

---

### 🧑‍🎓 Students & Data Scientists

Build ML models, explore project data, and contribute data science work using pyoso

<div className="category-cards">
  <a href={paths.cohortAnalysis} className="mini-card">
    <h3>👥 Cohort Analysis</h3>
    <p>Track a cohort of projects across a set of metrics over time</p>
  </a>
  <a href={paths.predictiveModelStarter} className="mini-card">
    <h3>📈 Forecasting</h3>
    <p>Leverage timeseries models to estimate how metrics will change over time</p>
  </a>
  <div className="mini-card disabled">
    <h3>🛡️ Trusted Users <em>(coming&nbsp;soon)</em></h3>
    <p>Train models to classify users on the basis of different trust signals</p>
  </div>
</div>

---

### 🧠 Researchers

Conduct advanced analysis on OSS ecosystems, governance networks, and funding trends

<div className="category-cards">
  <div className="mini-card disabled">
    <h3>⭐ OpenRank <em>(coming&nbsp;soon)</em></h3>
    <p>Run OpenRank on top of any network graph with your own trust seed assumptions</p>
  </div>
  <div className="mini-card disabled">
    <h3>🔬 Causal Inference <em>(coming&nbsp;soon)</em></h3>
    <p>Estimate the causal effect of grants on TVL and users using synthetic controls</p>
  </div>
  <a className="mini-card disabled">
    <h3>🏛️ Economic Simulation Sandbox <em>(coming&nbsp;soon)</em></h3>
    <p>Model government policies, market cycles, and GDP dynamics</p>
  </a>
</div>

---

### Looking for something else?

Check out our [Colab community folder](https://drive.google.com/drive/folders/1mzqrSToxPaWhsoGOR-UVldIsaX1gqP0F?usp=sharing) or browse our [GitHub Repository](https://github.com/opensource-observer/insights) to find work by our community.

Still can't find what you need? We're here to help—feel free to [open an issue](https://github.com/opensource-observer/insights/issues), fork the repo, or [join our Discord](https://discord.gg/7Rj9WXeS) and reach out to us!

---

<style>
{`
  /* flex container for cards */
  .category-cards {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin: 0.75rem 0 1.5rem;
  }
  @media (min-width: 600px) {
    .category-cards {
      flex-direction: row;
      align-items: stretch;
    }
  }

  /* card styling */
  .mini-card {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: transform 0.15s ease-in-out;
  }
  .mini-card:hover {
    transform: translateY(-2px);
  }
  .mini-card.disabled {
    opacity: 0.6;
    pointer-events: none;
  }

  /* text inside cards */
  .mini-card h3 {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 600;
  }
  .mini-card p {
    margin: 0.25rem 0 0;
    font-size: 0.85rem;
  }
`}
</style>
