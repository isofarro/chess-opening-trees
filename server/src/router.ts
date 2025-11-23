import type { FastifyInstance } from "fastify";
import type { OpeningTreeService } from "./services/openingTreeService";

export function registerRoutes(
	app: FastifyInstance,
	services: Record<string, OpeningTreeService>,
) {
	app.get("/", async () => {
		return Object.keys(services).map((name) => ({ name, path: `/${name}/` }));
	});

	app.get<{ Params: { treeName: string } }>(
		"/:treeName/*",
		async (request, reply) => {
			const treeName = request.params.treeName;
			const params = request.params as unknown as Record<string, string>;
			const encodedFen = params["*"] as string;
			const service = services[treeName];
			if (!service) {
				reply.code(404);
				return { detail: `Tree '${treeName}' not found` };
			}
			const fen = decodeURIComponent(encodedFen);
			const result = service.queryPosition(fen);
			if (!result) {
				reply.code(404);
				return { detail: `Position not found: ${fen}` };
			}
			return result;
		},
	);
}
