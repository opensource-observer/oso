import { EmbeddedSandbox } from "../../components/widgets/apollo-sandbox";
import styles from "./graphql.module.css";

export const dynamic = "force-static";
export const revalidate = false; // 3600 = 1 hour

export default function ApolloSandboxPage() {
  return (
    <div style={{ minHeight: "100vh" }}>
      <EmbeddedSandbox className={styles.embed} />
    </div>
  );
}
