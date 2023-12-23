import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import Heading from "@theme/Heading";

import styles from "./index.module.css";

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx("hero hero--primary", styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/contributing/intro"
          >
            Contribute to OSO
          </Link>

          <Link
            className="button button--secondary button--lg"
            to="/docs/datasets/intro"
          >
            Explore OSO Datasets
          </Link>
          <Link
            className="button button--secondary button--lg"
            to="/docs/api/intro"
          >
            Get API Access
          </Link>
          <Link
            className="button button--secondary button--lg"
            to="/docs/metrics/intro"
          >
            Learn About OSO Impact Metrics
          </Link>
          <Link
            className="button button--secondary button--lg"
            to="/docs/ecosystems/intro"
          >
            See OSO Coverage by Ecosystem
          </Link>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro"
          >
            Read More About OSO
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`Hello from ${siteConfig.title}`}
      description="This the OSO documentation site."
    >
      <HomepageHeader />
    </Layout>
  );
}
