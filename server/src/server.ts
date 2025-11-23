import Fastify from "fastify";
import { loadConfigFromEnv, resolveTreePath } from "./config";
import { OpeningTreeRepository } from "./repository/openingTreeRepository";
import { registerRoutes } from "./router";
import { OpeningTreeService } from "./services/openingTreeService";

async function main() {
  const app = Fastify({ logger: true });

  const { trees, baseDir, baseUrl } = loadConfigFromEnv();
  const services: Record<string, OpeningTreeService> = {};
  for (const { name, file } of trees) {
    const resolved = resolveTreePath(baseDir, file);
    const repo = new OpeningTreeRepository(resolved);
    services[name] = new OpeningTreeService(repo);
  }

  registerRoutes(app, services, baseUrl);

  const port = Number(process.env.PORT || 8000);
  const host = process.env.HOST || "0.0.0.0";
  await app.listen({ port, host });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
