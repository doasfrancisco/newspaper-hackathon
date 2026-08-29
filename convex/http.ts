import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";

const http = httpRouter();

const serve = httpAction(async (ctx, request) => {
  const runId = new URL(request.url).pathname.replace(/^\/paper\/?/, "");
  const edition =
    runId && runId !== "latest"
      ? await ctx.runQuery(api.editions.byRun, { runId })
      : await ctx.runQuery(api.editions.latest, {});
  if (!edition) {
    return new Response("No edition found", { status: 404 });
  }
  return new Response(edition.html, {
    status: 200,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
});

http.route({ pathPrefix: "/paper/", method: "GET", handler: serve });
http.route({ path: "/paper", method: "GET", handler: serve });

export default http;
