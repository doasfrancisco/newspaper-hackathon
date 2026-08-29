import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  editions: defineTable({
    runId: v.string(),
    dateLine: v.string(),
    postsRead: v.number(),
    keptCount: v.number(),
    html: v.string(),
  }).index("by_run", ["runId"]),
});
