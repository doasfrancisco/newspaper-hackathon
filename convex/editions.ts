import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const publish = mutation({
  args: {
    runId: v.string(),
    dateLine: v.string(),
    postsRead: v.number(),
    keptCount: v.number(),
    html: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("editions")
      .withIndex("by_run", (q) => q.eq("runId", args.runId))
      .unique();
    if (existing) {
      await ctx.db.patch(existing._id, args);
      return existing._id;
    }
    return await ctx.db.insert("editions", args);
  },
});

export const byRun = query({
  args: { runId: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("editions")
      .withIndex("by_run", (q) => q.eq("runId", args.runId))
      .unique();
  },
});

export const latest = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("editions").order("desc").first();
  },
});
