import fs from "node:fs";
import path from "node:path";
import type { ServerConfig, TreeConfigItem } from "./types";

export function loadConfigFromEnv(): {
  trees: TreeConfigItem[];
  baseDir: string;
  baseUrl?: string;
} {
  const configPath = process.env.OPENING_TREE_CONFIG;
  if (!configPath) {
    throw new Error(
      "No config file specified. Set OPENING_TREE_CONFIG environment variable.",
    );
  }
  const resolved = path.isAbsolute(configPath)
    ? configPath
    : path.resolve(configPath);
  const raw = fs.readFileSync(resolved, "utf8");
  const json: ServerConfig = JSON.parse(raw);
  const trees = Array.isArray(json.trees) ? json.trees : [];
  if (!trees.length) throw new Error("No trees specified in config file.");
  return { trees, baseDir: path.dirname(resolved), baseUrl: json.baseUrl };
}

export function resolveTreePath(baseDir: string, treePath: string): string {
  if (path.isAbsolute(treePath)) return treePath;
  return path.resolve(baseDir, treePath);
}
